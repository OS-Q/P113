import sys
from os.path import isfile, join

from SCons.Script import Import, Return

Import("env")

board = env.BoardConfig()
platform = env.PioPlatform()
core = board.get("build.core", "")


def get_suitable_optiboot_binary(framework_dir, board_config):
    mcu = board_config.get("build.mcu", "").lower()
    f_cpu = board_config.get("build.f_cpu", "16000000L").upper()
    uart = board_config.get("hardware.uart", "uart0").upper()
    bootloader_led = board_config.get("bootloader.led_pin", "").upper()
    if core == "MightyCore" and board_config.get("build.variant", "") == "bobuino":
        bootloader_led = "B7"
    bootloader_file = "optiboot_flash_%s_%s_%s_%s_%s.hex" % (
        mcu,
        uart,
        board_config.get("bootloader.speed", env.subst("$UPLOAD_SPEED")),
        f_cpu,
        bootloader_led,
    )
    bootloader_path = join(
        framework_dir,
        "bootloaders",
        "optiboot_flash",
        "bootloaders",
        mcu,
        f_cpu,
        bootloader_file,
    )

    if isfile(bootloader_path):
        return bootloader_path

    return bootloader_path.replace(".hex", "_BIGBOOT.hex")


framework_dir = ""
if env.get("PIOFRAMEWORK", []):
    framework_dir = platform.get_package_dir(
        platform.frameworks[env.get("PIOFRAMEWORK")[0]]["package"]
    )

bootloader_path = board.get("bootloader.file", "")
if core in ("MiniCore", "MegaCore", "MightyCore", "MajorCore"):
    if not isfile(bootloader_path):
        bootloader_path = get_suitable_optiboot_binary(framework_dir, board)
else:
    if not isfile(bootloader_path):
        bootloader_path = join(framework_dir, "bootloaders", bootloader_path)

    if not board.get("bootloader", {}):
        sys.stderr.write("Error: missing bootloader configuration!\n")
        env.Exit(1)

if not isfile(bootloader_path):
    sys.stderr.write("Error: Couldn't find bootloader image %s\n" % bootloader_path)
    env.Exit(1)

fuses_action = env.SConscript("fuses.py", exports="env")

lock_bits = board.get("bootloader.lock_bits", "0x0F")
unlock_bits = board.get("bootloader.unlock_bits", "0x3F")

env.Replace(
    BOOTUPLOADER="avrdude",
    BOOTUPLOADERFLAGS=[
        "-p",
        "$BOARD_MCU",
        "-C",
        '"%s"'
        % join(env.PioPlatform().get_package_dir("tool-avrdude") or "", "avrdude.conf"),
    ],
    BOOTFLAGS=['-Uflash:w:"%s":i' % bootloader_path, "-Ulock:w:%s:m" % lock_bits],
    UPLOADBOOTCMD="$BOOTUPLOADER $BOOTUPLOADERFLAGS $UPLOAD_FLAGS $BOOTFLAGS",
)

if env.subst("$UPLOAD_PROTOCOL") != "custom":
    env.Append(BOOTUPLOADERFLAGS=["-c", "$UPLOAD_PROTOCOL"])
else:
    print(
        "Warning: The `custom` upload protocol is used! The upload and fuse flags may "
        "conflict!\nMore information: "
        "https://docs.platformio.org/en/latest/platforms/atmelavr.html"
        "#overriding-default-bootloader-command\n"
    )

bootloader_actions = [
    fuses_action,
    env.VerboseAction("$UPLOADBOOTCMD", "Uploading bootloader"),
]

Return("bootloader_actions")
