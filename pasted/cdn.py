import functools
import time

from openstack import connection as os_conn

from pasted import app
from pasted import log
from pasted import exceptions


class OpenStack(object):
    """Class for reusable OpenStack utility methods."""

    def __init__(self, container):
        """Initialization method for class.

        :param container: Name of the container to upload into.
        :type container: str
        """

        self.container = container or app.config['CDN_CONTAINER_NAME']
        self.os_auth_args = {
            'username': app.config['OS_USERNAME'],
            'password': app.config['OS_PASSWORD'],
            'tenant_name': app.config['OS_TENANT_NAME'],
            'user_domain_name': app.config['OS_USER_DOMAIN_NAME'],
            'project_name': app.config['OS_PROJECT_NAME'],
            'project_domain_name': app.config['OS_PROJECT_DOMAIN_NAME'],
            'auth_url': app.config['OS_AUTH_URL'],
            'region_name': app.config['OS_REGION_NAME'],
            'insecure': app.config['OS_INSECURE'],
            'interface': app.config['OS_INTERFACE']
        }
        self.verify = self.os_auth_args['insecure'] is False
        self.os_auth_args = {
            k: v for k, v in self.os_auth_args.items() if v is not None
        }

    @property
    def conn(self):
        """Return an OpenStackSDK connection.

        :returns: object
        """
        return os_conn.Connection(verify=self.verify, **self.os_auth_args)

    def object_upload(self, key, content):
        """Upload content to a container and return its object.

        :param key: File object name.
        :type key: str
        :param content: File content.
        :type content: str
        :returns: object
        """
        return self.conn.object_store.upload_object(
            container=self.container,
            name=key,
            data=content
        ).etag

    def object_count(self):
        """Return the object count and size of a given container.

        The returned object is (<count>, <size>)
            Size is returned in bytes.

        :returns: tuple
        """
        container = self.conn.get_container(name=self.container)
        log.info('container information: %s' % container)
        return int(container['X-Container-Object-Count']), int(container['X-Container-Bytes-Used'])


@exceptions.retry(ExceptionToCheck=Exception)
def upload(key, content, container=None):
    """Upload content to a CDN provider.

    :param key: File object name.
    :type key: str
    :param content: File content.
    :type content: str or bytes
    :returns: str
    """
    if app.config['CDN_PROVIDER'] == 'openstack':
        cdn_provider = OpenStack(container=container)
        return cdn_provider.object_upload(key=key, content=content)


@exceptions.retry(ExceptionToCheck=Exception)
def count(container=None):
    """Count uploaded content to a CDN provider.

    :returns: int
    """
    if app.config['CDN_PROVIDER'] == 'openstack':
        cdn_provider = OpenStack(container=container)
        return cdn_provider.object_count()
