from setuptools import setup, find_packages


VERSION = "0.0.0"
URL = "https://github.com/johnboxall/dpod/"
DOWNLOAD_URL = (URL + "tarball/" + VERSION)

setup(name="dpod",
      version=VERSION,
      description="CLI for deploying a private GitHub repository to Heroku.",
      long_description=open('README.md').read(),
      scripts=["dpod"],
      author="John Boxall",
      author_email="john@mobify.com",
      url=URL,
      license="MIT",
      install_requires=open("requirements.pip").read())