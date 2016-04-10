from ipykernel.kernelbase import Kernel as BaseKernel
from sqlalchemy import create_engine
import sqlparse
import re


class SqlKernel(BaseKernel):

    implementation = 'sql_kernel'
    implementation_version = '0.1'
    banner = 'SQL Kernel ' + implementation_version
    language_version = 'SQL:2011'

    language_info = {
        'name': 'sql',
        'mimetype': 'application/octet-stream',
        'file_extension': '.sql'
    }

    def __init__(self, **kwargs):
        super(SqlKernel, self).__init__(**kwargs)

        self.__sql_engine = None
        self.__sql_connection = None

    def do_execute(self, code, silent=False, store_history=True, user_expressions=None, allow_stdin=False):

        code_parts = re.split(R'(^[ \t]*!.+;$)', code, flags=re.MULTILINE)

        try:
            for part in code_parts:
                part = part.strip()

                if part.startswith('!') and part.endswith(';'):
                    connection_str = part.rstrip('!').lstrip(';').strip()
                    self.__process_connection_str(connection_str)
                else:
                    self.__process_sql_part(part, silent)
        except Exception as e:
            error_content = {
                'execution_count': self.execution_count,
                'ename': '',
                'evalue': str(e),
                'traceback': ''
            }
            self.send_response(self.iopub_socket, 'error', error_content)
            error_content['status'] = 'error'
            return error_content

        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {}
        }

    def __process_connection_str(self, connection_string):
        if self.__sql_connection is not None:
            self.__sql_connection.close()
            self.__sql_connection = None
            self.__sql_engine = None

        # TODO: try if ok
        eng = create_engine(connection_string)
        con = eng.connect()

        self.__sql_engine = eng
        self.__sql_connection = con

    def __process_sql_part(self, code, silent):
        if self.__sql_connection is None:
            # TODO
            pass

        statements = sqlparse.split(code)

        for statement in statements:
            self.__sql_connection.execute(statement)

            # TODO

            if not silent:
                stream_content = {'name': 'stdout', 'text': 'OK'}
                self.send_response(self.iopub_socket, 'stream', stream_content)


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=SqlKernel)
