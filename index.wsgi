import sae
# sae.add_vendor_dir('packages')

from coursearea import wsgi

application = sae.create_wsgi_app(wsgi.application)
