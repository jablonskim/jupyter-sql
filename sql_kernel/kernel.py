from ipykernel.kernelbase import Kernel as BaseKernel


class SqlKernel(BaseKernel):

    def __init__(self, **kwargs):
        super(SqlKernel, self).__init__(**kwargs)

    # TODO
