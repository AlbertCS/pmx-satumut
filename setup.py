"""pmx: a toolkit for free-energy calculation setup/analysis and
biomolecular structure handling.

For installation type the command::
  python setup.py install
or
  pip install .
"""

from setuptools import setup, Extension
import versioneer


def readme():
    with open('README.rst') as f:
        return f.read()

# ----------
# Extensions
# ----------
pmx = Extension('pmx._pmx',
                libraries=['m'],
                include_dirs=['src/pmx/extensions/pmx'],
                sources=['src/pmx/extensions/pmx/Geometry.c',
                         'src/pmx/extensions/pmx/wrap_Geometry.c',
                         'src/pmx/extensions/pmx/init.c',
                         'src/pmx/extensions/pmx/Energy.c']
                )

xdrio = Extension('pmx._xdrio',
                  libraries=['m'],
                  include_dirs=['src/pmx/extensions/xdr'],
                  sources=['src/pmx/extensions/xdr/xdrfile.c',
                           'src/pmx/extensions/xdr/xdrfile_trr.c',
                           'src/pmx/extensions/xdr/xdrfile_xtc.c']
                  )
extensions = [pmx, xdrio]

# -----
# Setup
# -----
setup(name='pmx-satumut',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Toolkit for free-energy calculation setup/analysis '
                  'and biomolecular structure handling',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
      ],
      url='https://github.com/AlbertCS/pmx-satumut/tree/develop',
      author='Daniel Seeliger',
      author_email='seeliger.biosoft@gmail.de',
      license='GPL 3',
      packages=['pmx'],
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      ext_modules=extensions,
      tests_require=['pytest'],
      install_requires=['numpy', 'scipy', 'matplotlib', 'future'],
      python_requires=">=3.6",
      entry_points={'console_scripts': ['pmx = pmx.scripts.cli:entry_point']},
      )
