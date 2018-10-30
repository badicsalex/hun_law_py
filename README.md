# law-tools

A small project for parsing Hungarian Law. It does the following thigs:

* Parse PDF files into lines using pdfminer. It does so much more accurately
  than other pdf2txt implementations.
* Parse "Magyar Közlöny" PDFs into individual Acts
* Separate Acts into structural elements (Articles, subpoints, etc.)

Things planned:

* Parse reference strings
* Parse amendments and create the applicable set of laws for any given time
* Export into a linked, interactive HTML format
* Export into Akoma Ntoso format
