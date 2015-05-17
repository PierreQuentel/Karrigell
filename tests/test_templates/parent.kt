<html>
<head>
<title>KT test</title>
</head>
<body>
<h1>Variable Interpolation</h1>
<p>$$data.var = $data.var
<p>$$this.root_url = $this.root_url
<hr>
<h1>Translation test</h1>
<p>Direct translation of text in template:
<p>__[phrase to translate]: _[phrase to translate]
<p>Translation of text held in a variable
<p>__[$$data.phrase]: _[$data.phrase]
<hr>
<h1>Inclusion Tests</h1>
Including sibling.kt in parent.kt:
@[sibling.kt]
<hr>
Including children/child.kt in parent.kt:
@[children/child.kt]
<hr>
Including children/grandchildren/grandchild.kt in parent.kt:
@[children/grandchildren/grandchild.kt]
<hr>
Including children/grandchildren/grandchild.kt in parent.kt (again):
@[children/grandchildren/grandchild.kt]
<hr>
</body>
</html>