import datetime
import sys
from distutils.version import LooseVersion

from workflow import Workflow3, web, ICON_WEB

CACHE_TTL = 600
PYPI_PACKAGE_URL = 'https://pypi.python.org/pypi/{package_name}/json'

logger = None


def file_size(num):
    for unit in ['', 'K', 'M', 'G']:
        if abs(num) < 1024.0:
            return "%3.1f%sB" % (num, unit)
        num /= 1024.0
    return "%.1fB" % num


def get_package_versions(package_name):
    url = PYPI_PACKAGE_URL.format(package_name=package_name)
    response = web.get(url)
    if response.status_code == 404:
        # Some queries won't have packages, no big deal
        return None
    logger.info('Got package info for {}'.format(package_name))
    return response.json()


def format_subtitle(release):
    upload_time = datetime.datetime.strptime(release['upload_time'], "%Y-%m-%dT%H:%M:%S")
    formatted_datetime = upload_time.strftime('%b. %d, %Y')
    return u'Released on {release_date} \u2022 {size} size \u2022 {downloads} downloads'.format(
        release_date=formatted_datetime,
        downloads=release['downloads'],
        size=file_size(release['size'])
    )


def main(wf):
    package_name = None
    if len(wf.args):
        package_name = wf.args[0]

    if package_name:
        def wrapper():
            return get_package_versions(package_name)

        cache_name = 'package-data-{package_name}'.format(
            package_name=package_name
        )
        package_data = wf.cached_data(cache_name, wrapper, max_age=CACHE_TTL)

        if package_data:
            for version, releases in sorted(package_data['releases'].iteritems(),
                                            key=lambda p: LooseVersion(p[0]),
                                            reverse=True):
                title = '{package_name}=={version}'.format(
                    package_name=package_name,
                    version=version
                )
                subtitle = ''
                if len(releases) > 0:
                    subtitle = format_subtitle(releases[0])
                package_version_url = package_data['info']['package_url'] + version
                wf.add_item(
                    title=title,
                    subtitle=subtitle,
                    arg=package_version_url,
                    icon=ICON_WEB,
                    valid=True
                )

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    logger = wf.logger
    sys.exit(wf.run(main))
