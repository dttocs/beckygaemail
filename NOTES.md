

Set up CORS so XmlHttpRequest actually works:

- [google app engine - CORS - Using AJAX to post on a Python (webapp2) web service - Stack Overflow](http://stackoverflow.com/questions/18760224/cors-using-ajax-to-post-on-a-python-webapp2-web-service)
- [Using CORS - HTML5 Rocks](http://www.html5rocks.com/en/tutorials/cors/)
- [enable cross-origin resource sharing](http://enable-cors.org/server_appengine.html)
- [javascript - Chrome shows Access Control Allow Origin error - Stack Overflow](http://stackoverflow.com/questions/19001107/chrome-shows-access-control-allow-origin-error)

[python - parsing json formatted requests in appengine](http://stackoverflow.com/questions/12091028/parsing-json-formatted-requests-in-appengine)

Check options to confirm CORS is correct:

	curl -v -X OPTIONS http://beckygaemail.appspot.com/complete

Verify what cURL is actually sending:

	curl -v -d content='{"completion": "N", "first_name": "Rebecca", "last_name": "Hogue", "email": "r@b.com"}' \
 	http://beckygaemail.appspot.com/complete --trace-ascii /dev/stdout

Fix it so it's just JSON:

	curl -v -d '{"completion": "N", "first_name": "Bob", "last_name": "Hogue", "email": "r@h.com"}' \
	http://bccqualitymodules.appspot.com/complete

Note that this doesn't actually set the content-type header correctly, but this naive code doesn't check.