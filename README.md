# Karrigell
Web framework for Python 3

*This project is not maintained any more. When it started in 2002 there were
very few lightweight web frameworks; now there are many popular options, that
are more complete and better designed than Karrigell.*

## 1. Package installation

One you have downloaded the package and unzipped it in a directory, open a
console window, go to the directory and run :

```
python setup.py install
```

This will install the packages Karrigell and HTMLTags in the Python
distribution.

## 2. Start the built-in server

In another directory, save these 2 lines in a script called server.py :

```
import Karrigell
Karrigell.run()
```

This will start a built-in web server, listening for request on port 80.
If you want another port, change the second line to :

```
Karrigell.run(port=8080)
```

By default, the server serves the file in its folder. That is, if you put
an image file picture.jpg in the same folder as server.py, and enter
`http://localhost/picture.jpg` in a web browser, the server will print this
image.

The documentation explains how to serve different applications in different
directories.

## 3. Write a script

In the same directory as server.py, save these 2 lines in index.py :

```python
def index():
    return "Hello, world"
```

Enter `http://localhost/index.py/index` in the browser, you will see the
message "Hello, world".

That's all it takes ! You can now browse the documentation to see how to
develop applications, control access to users, manage sessions, localize
your scripts, etc.