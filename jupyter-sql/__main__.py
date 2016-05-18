from ipykernel.kernelapp import IPKernelApp
from .kernel import SqlKernel
IPKernelApp.launch_instance(kernel_class=SqlKernel)
