# -*- mode: python -*-
#
# Expects directories to be individual modules
# Will ignore expr: ".*" directories and files at top layer
#
#--------------------------#
import random
import string
from pathlib import Path

_BIN_NAME = "ec"
_DEFAULT_VAR_LEN = 4


def module_dir():
    return (Path(__file__).absolute().parents[1]) / "modules"


def _random_var_name(length=_DEFAULT_VAR_LEN):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def generate_analysis_block(var_name, full_path):
    hiddenimports = ['encodings']
    return """
{var_name} = Analysis(
    ['{full_path}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports={hiddenimports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

""".format(var_name=var_name, full_path=full_path, hiddenimports=hiddenimports)


def generate_pyz_block(var_name):
    return f"""
{var_name}_pyz = PYZ({var_name}.pure, {var_name}.zipped_data, cipher=None)\n
""".format(var_name=var_name)


def generate_exe_block(var_name, module_name, file_name):
    return """
{var_name}_exe = EXE(
    {var_name}_pyz,
    {var_name}.scripts,
    {var_name}.binaries,
    {var_name}.zipfiles,
    {var_name}.datas,
    [],
    name='{bin_name}_{module_name}_{file_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)

""".format(var_name=var_name,
           bin_name=_BIN_NAME,
           module_name=module_name,
           file_name=file_name)


def generate_spec_file(module_name, spec_data):
    spec_content = ""

    ## build valid .spec file for module to be consumed by pyinstaller

    # write analysis blocks first
    spec_content = "".join([v['analysis'] for _, v in spec_data.items()])

    ## write MERGE statement
    #merge = "MERGE( "
    #for v in spec_data.values():
    #    merge += f"({v['var_name']}, '{v['stem']}', '{v['bin_name']}'),"
    #merge += ")\n"

    #spec_content += merge

    # write pyz
    spec_content += "".join([v['pyz'] for v in spec_data.values()])

    # write exe
    spec_content += "".join([v['exe'] for v in spec_data.values()])

    spec_path = Path(f"/tmp/{module_name}.spec")

    print("Writing {} to {}".format(spec_path.name, spec_path.absolute()))
    # finally -- write to file always to /tmp/
    with open(spec_path, "w") as f:
        f.write(spec_content)


def main():
    for module in module_dir().iterdir():
        if not module.is_dir() or module.name[0] == ".":
            continue

        spec_data = {}

        for file in module.iterdir():
            if not file.is_file():
                continue

            var_name = _random_var_name()
            analysis = generate_analysis_block(var_name, file.absolute())
            pyz = generate_pyz_block(var_name)
            exe = generate_exe_block(var_name, module.name, file.stem)

            spec_data[file.stem] = {
                'var_name': var_name,
                'stem': file.stem,
                'bin_name': f"{_BIN_NAME}_{module.name}_{file.stem}",
                "analysis": analysis,
                "pyz": pyz,
                "exe": exe
            }

        generate_spec_file(module.name, spec_data)


if __name__ == "__main__":
    main()
