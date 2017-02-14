<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  % if 'title' in page:
  <title>${page['title']}</title>
  % endif
  % if 'description' in page:
  <meta name="description" content="${page['description']}">
  % endif
  % if 'author' in page:
  <meta name="author" content="${page['author']}">
  % endif
  <link rel="stylesheet" href="${page['folders']['css']}/site.css">
</head>
<body>
  ${body}
</body>
</html>
