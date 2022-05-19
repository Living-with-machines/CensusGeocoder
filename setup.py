import setuptools

setuptools.setup(
    name="historic-census-gb-geocoder",
    version="n/a",
    description="Geocodes Historic Great British Census Data 1851-1911",
    author=u"josh-rhodes",
    #author_email="",
    license="MIT License",
    keywords=["britain", "streets", "census", "living with machines"],
    long_description = open('README.md', encoding="utf8").read(),
    long_description_content_type = 'text/markdown',
    zip_safe = False,
    url="",
    download_url="",
    packages = setuptools.find_packages(),
    include_package_data = True,
    platforms="",
    python_requires='>=3.7',
    install_requires=[
        "numpy>=1.21.5",
        "pandas>=1.3.4",
        "Shapely>=1.8.0",
        "scikit-learn>=1.0.1",
		"geopandas>=0.9.0",
		"pygeos>=0.10.2",
		"recordlinkage>=0.14",
		"rapidfuzz>=1.5.0"
    ]



    
)