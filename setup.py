import setuptools

setuptools.setup(
    name="tango-modbus-simulator",
    version="0.1.0",
    author="Sebastian Jennen",
    author_email="sj@imagearts.de",
    description="tango-modbus-simulator device driver",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    scripts=['ModbusSimulator.py']
)