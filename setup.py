
from distutils.core import setup
import py2exe, sys, os


output = "bin"
excludes = ["MSVCR71.dll"]
orig = py2exe.build_exe.isSystemDLL
py2exe.build_exe.isSystemDLL = lambda p: 0 if os.path.basename(p) in excludes else orig(p)

class Py2exe(py2exe):

    def initialize_options(self):
        # Add a new "upx" option for compression with upx
        py2exe.initialize_options(self)
        self.upx = 0

    def copy_file(self, *args, **kwargs):
        # Override to UPX copied binaries.
        (fname, copied) = result = py2exe.copy_file(self, *args, **kwargs)

        basename = os.path.basename(fname)
        if (copied and self.upx and
            (basename[:6]+basename[-4:]).lower() != 'python.dll' and
            fname[-4:].lower() in ('.pyd', '.dll')):
            os.system('upx --best "%s"' % os.path.normpath(fname))
        return result

    def patch_python_dll_winver(self, dll_name, new_winver=None):
        # Override this to first check if the file is upx'd and skip if so
        if not self.dry_run:
            if not os.system('upx -qt "%s" >nul' % dll_name):
                if self.verbose:
                    print "Skipping setting sys.winver for '%s' (UPX'd)" % \
                          dll_name
            else:
                py2exe.patch_python_dll_winver(self, dll_name, new_winver)
                # We UPX this one file here rather than in copy_file so
                # the version adjustment can be successful
                if self.upx:
                    os.system('upx --best "%s"' % os.path.normpath(dll_name))
                    
setup(

    #cmdclass = {'py2exe': Py2exe},

    options = {
        "py2exe": {"optimize": 2, "bundle_files": 1, "dist_dir": output}
    },
    
    windows = [{
        "script": "slbuddy.py", "icon_resources": [(1, "sl.ico")]
    }]
    
    ,zipfile = None
    
)

for exclude in excludes:
    os.remove(os.path.join(os.path.dirname(__file__), output, exclude))