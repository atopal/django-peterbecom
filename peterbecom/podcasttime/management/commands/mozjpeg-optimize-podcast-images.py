import os
import subprocess

from django.conf import settings
from django.template.defaultfilters import filesizeformat

from peterbecom.base.basecommand import BaseCommand
from peterbecom.podcasttime.models import Podcast


def check_output(cmd):
    pipes = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    std_out, std_err = pipes.communicate()
    if pipes.returncode != 0:
        # an error happened!
        err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
        raise Exception(err_msg)
    return std_out.strip()


class Command(BaseCommand):

    def _handle(self, *args, **kwargs):
        qs = Podcast.objects.filter(image__isnull=False)
        savings = []
        skips = 0
        for podcast in qs.order_by('?')[:800]:
            try:
                path = podcast.image.path
            except ValueError:
                continue
            if not os.path.isfile(path):
                print("Not a file", path)
                continue
            log_file = path + '.mozjpeged'
            if os.path.isfile(log_file):
                skips += 1
                continue
            ext = os.path.splitext(path)[1]
            if not ext:
                continue
            if ext not in ('.jpg', '.jpeg'):
                # print('Unrecognized extension {!r}'.format(ext))
                continue

            if not os.path.isfile(path):
                print("Completely missing image path", path)
                podcast.image = None
                podcast.save()
                continue
            if not os.stat(path).st_size:
                print("Completely empty image", path)
                os.remove(path)
                podcast.image = None
                podcast.save()
                continue

            size_before = os.stat(path).st_size
            print(path)
            cmd = [
                settings.MOZJPEG_PATH,
                '-optimize',
                '-outfile', path,
                path,
            ]
            try:
                out = check_output(cmd)
            except Exception as exception:
                if 'Not a JPEG file' in str(exception):
                    continue
                else:
                    raise
            if out:
                self.warning(out)
            size_after = os.stat(path).st_size
            with open(log_file, 'w') as f:
                f.write(
                    'From {} bytes to {} bytes\n'.format(
                        format(size_before, ','),
                        format(size_after, ','),
                    )
                )
            savings.append(size_before - size_after)

        if savings:
            self.out("SUM savings:", filesizeformat(sum(savings)))
            avg = sum(savings) / len(savings)
            self.out("AVG savings:", filesizeformat(avg))

        self.out('{} skips'.format(skips))
