import setuptools

setuptools.setup(
    name='Rocinante',
    version='1.3.3',
    author='sui',
    author_email='2315375425@qq.com',
    description='Rocinante is a lightweight WSGI web application framework based on Werkzeug.',
    packages=setuptools.find_packages(),
    python_requires='>=3',
    install_requires=[
        "Werkzeug>=0.15",
    ]
)
