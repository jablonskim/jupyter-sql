from ipykernel.kernelbase import Kernel as BaseKernel
from sqlalchemy import create_engine
from sqlalchemy.exc import DatabaseError
import sqlparse
import re
from sys import exc_info
import traceback


class SqlKernel(BaseKernel):

    implementation = 'jupyter-sql'
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
        error_content = None

        try:
            for part in code_parts:
                part = part.strip()

                if part.startswith('!') and part.endswith(';'):
                    connection_str = part.rstrip(';').lstrip('!').strip()
                    self.__process_connection_str(connection_str)
                else:
                    self.__process_sql_part(part, silent)
        except DatabaseError as e:
            ex_type, ex, tb = exc_info()
            error_content = {
                'ename': str(ex_type),
                'evalue': str(e),
                'traceback': [str(e)]
            }
        except Exception as e:
            ex_type, ex, tb = exc_info()
            error_content = {
                'ename': str(ex_type),
                'evalue': str(e),
                'traceback': traceback.format_exception(ex_type, ex, tb)
            }

        if error_content is not None:
            error_content['execution_count'] = self.execution_count
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

        eng = create_engine(connection_string)
        con = eng.connect()

        self.__sql_engine = eng
        self.__sql_connection = con

    def __process_sql_part(self, code, silent):
        if len(code.strip()) == 0:
            return

        if self.__sql_connection is None:
            raise RuntimeError('SQL query before connection')

        statements = sqlparse.split(code)

        for statement in statements:
            result = self.__sql_connection.execute(statement)

            if not silent:
                text = None

                stmt_type = sqlparse.parse(statement)[0].get_type()

                if stmt_type == 'SELECT':
                    text = self.__process_select(result.keys(), result.fetchall())

                if stmt_type == 'INSERT':
                    text = 'Insert succeeded\n'

                if stmt_type == 'UPDATE':
                    text = 'Updated %d rows\n' % result.rowcount

                if stmt_type == 'DELETE':
                    text = 'Deleted %d rows\n' % result.rowcount

                if text is not None:
                    stream_content = {'name': 'stdout', 'text': text}
                    self.send_response(self.iopub_socket, 'stream', stream_content)

    def __process_select(self, keys, rows):
        columns_size = [0 for _ in range(len(keys))]

        for i, k in enumerate(keys):
            columns_size[i] = len(k)

        for row in rows:
            for i, k in enumerate(row):
                columns_size[i] = max(len(str(k)), columns_size[i])

        separator_line = '+'
        for i in range(len(columns_size)):
            separator_line += ('-' * (columns_size[i] + 2)) + '+'
        separator_line += '\n'

        text = 'Selected %d rows:\n' % len(rows)

        text += separator_line + '|'

        for i, k in enumerate(keys):
            text += ' ' + str(k) + ((columns_size[i] - len(str(k))) * ' ') + ' |'

        text += '\n' + separator_line

        for row in rows:
            text += '|'
            for i, k in enumerate(row):
                text += ' ' + str(k) + ((columns_size[i] - len(str(k))) * ' ') + ' |'
            text += '\n'

        text += separator_line + '\n'

        return text


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=SqlKernel)
