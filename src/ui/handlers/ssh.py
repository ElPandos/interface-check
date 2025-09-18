import paramiko


class Ssh:
    def __init__(self) -> None:
        pass

    def __run_remote(self) -> None:
        # ---------- SSH Jumphost ----------
        jump_host = "137.58.231.134"
        jump_user = "emvekta"
        jump_pass = "emvekta"

        # ---------- Final Target ----------
        target_host = "172.16.87.1"
        target_user = "emvekta"
        target_pass = "emvekta"

        # Connect to jumphost first
        jump_ssh = paramiko.SSHClient()
        jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_ssh.connect(
            jump_host,
            username=jump_user,
            password=jump_pass,
            look_for_keys=False,
            allow_agent=False,
        )

        # Open a channel from jumphost -> target
        jump_transport = jump_ssh.get_transport()
        dest_addr = (target_host, 22)
        local_addr = (jump_host, 22)
        channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        # Connect to the final target through that channel
        target_ssh = paramiko.SSHClient()
        target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target_ssh.connect(
            target_host,
            username=target_user,
            password=target_pass,
            sock=channel,  # <--- magic happens here
            look_for_keys=False,
            allow_agent=False,
        )

        # Run your command on the target host
        stdin, stdout, stderr = target_ssh.exec_command("ip addr")
        stdout_str = stdout.read().decode()
        stderr_str = stderr.read().decode()

        target_ssh.close()
        jump_ssh.close()

        self.debug(f"Run remote - STDOUT: {stdout_str}")
        self.debug(f"Run remote - STDERR: {stderr_str}")
