import paramiko
import psycopg2


def install_postgresql(ssh_host, ssh_port, ssh_user, ssh_password):
    try:
        # Подключение по SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, port=ssh_port,
                    username=ssh_user, password=ssh_password)
        print("Успешное подключение к серверу")

        stdin, stdout, stderr = ssh.exec_command(
            'sudo -S sh -c \'echo \"deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main\" > /etc/apt/sources.list.d/pgdg.list\'')
        execute_command_from_sudo(ssh_password, stdout, stdin)
        print("Репозиторий успешно добавлен")

        stdin, stdout, stderr = ssh.exec_command(
            'wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo -S apt-key add -')
        execute_command_from_sudo(ssh_password, stdout, stdin)
        print("Ключ репозитория успешно импортирован")

        print("Установка последней версии PostgreSQL")
        stdin, stdout, stderr = ssh.exec_command(
            'sudo -S apt update && sudo apt install -y postgresql && psql --version')
        execute_command_from_sudo(ssh_password, stdout, stdin)

        # Закрытие соединения
        ssh.close()
        return True
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False


def execute_command_from_sudo(ssh_password, stdout, stdin):
    stdin.write(ssh_password + "\n")
    stdin.flush()

    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            alldata = stdout.channel.recv(1024)
            prevdata = b"1"

            while prevdata:
                prevdata = stdout.channel.recv(1024)
                alldata += prevdata
                print(str(alldata, "utf8"))


def configure_postgresql_for_external_connections(ssh_host, ssh_port, ssh_user, ssh_password):
    try:
        # Подключение по SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, port=ssh_port,
                    username=ssh_user, password=ssh_password)

        stdin, stdout, stderr = ssh.exec_command(
            "sudo -S sh -c \"echo \'listen_addresses= \'\\'*\\' >> /etc/postgresql/16/main/postgresql.conf\"")
        execute_command_from_sudo(ssh_password, stdout, stdin)

        stdin, stdout, stderr = ssh.exec_command(
            'sudo -S sh -c \'echo \"host all all 0.0.0.0/0 trust\" >> /etc/postgresql/16/main/pg_hba.conf\'')
        execute_command_from_sudo(ssh_password, stdout, stdin)

        stdin, stdout, stderr = ssh.exec_command(
            'sudo -S sh -c \'systemctl restart postgresql\'')
        execute_command_from_sudo(ssh_password, stdout, stdin)

        print("Конфигурация PostgreSQL изменена для приема внешних соединений.")

        ssh.close()
        return True
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False


def check_postgresql(dbname, user, password, host, port=5433):
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(
            dbname=dbname,
            user='postgres',
            password='postgres',
            host=host,
            port=port
        )

        cur = conn.cursor()

        # Выполнение запроса
        cur.execute('SELECT 1')

        # Получение результата
        result = cur.fetchone()
        if result and result[0] == 1:
            print("PostgreSQL работает корректно.")
        else:
            print("Ошибка: PostgreSQL не вернул ожидаемый результат.")

        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == '__main__':
    ssh_port = 22
    ssh_user = 'username'
    ssh_password = 'userpassword'
    dbname = 'postgres'

    db_host = input("Введите ip адрес или имя хоста: ")

    install_postgresql(db_host, ssh_port, ssh_user, ssh_password)

    configure_postgresql_for_external_connections(db_host, ssh_port, ssh_user, ssh_password)

    check_postgresql(dbname, ssh_user, ssh_password, db_host)
