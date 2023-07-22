
Development
===========

The source code can be found on the |pygeoops git repository|.

If you want to do feature requests or file bug reports, that's the place to 
be as well.

Create development environment
------------------------------

The first step would be Now, if you fork the |pygeoops git repository|, you should be able to run/debug the code.

If you don't have the conda package manager installed yet, here is a link to the 
`miniforge installer`_


Then you'll need to create a new conda environment with the necessary 
dependencies::

    conda env create -f environment-dev.yml
    conda activate pygeoops-dev


.. _miniforge installer : https://github.com/conda-forge/miniforge#miniforge3

.. |pygeoops git repository| raw:: html

   <a href="https://github.com/pygeoops/pygeoops" target="_blank">pygeoops git repository</a>
