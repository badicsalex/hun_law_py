# Hun-Law

A small project for parsing Hungarian Law. It does the following thigs:

* Parse PDF files into lines using pdfminer. It does so much more accurately
  than other pdf2txt implementations.
* Parse "Magyar Közlöny" PDFs into individual Acts
* Separate Acts into structural elements (Articles, subpoints, etc.)
* Parse internal and external references in legal text
* Parse special phrases like amendments and repeals into easy-to-use objects
* Generate simple TXT, JSON and HTML version of the parsed documents

## Usage

After cloning the repository, simply run `./generate_output.py`:

```
./generate_output.py txt 2013/31
./generate_output.py json 2018/123 --output-dir /tmp/acts_as_json
```

Interesting Magyar Közlöny issues can be found in `act_to_mk_issue.csv`

To be able to actually use html output, you will have to copy or symlink the
style.css:
```
./generate_output.py html 2014/91 2014/92 2014/93 --output-dir /var/www/hun_law
cp style.css /var/www/hun_law
```


## Things planned:

* Export into Akoma Ntoso format
* Export into epub or mobi format

## Contribution

Feel free to open issues for feature reqests or found bugs. Merge Requests are more than welcome too, as long as all tests and static analysis passes.
