import sys
from os.path import join

from SCons.Script import COMMAND_LINE_TARGETS, Import, Return

Import("env")


def get_lfuse(target, f_cpu, oscillator, bod, eesave, ckout):
    targets_2 = (
        "atmega328pb",
        "atmega324pb",
        "atmega168pb",
        "atmega162",
        "atmega88pb",
        "atmega48pb",
        "at90can128",
        "at90can64",
        "at90can32",
    )

    ckout_bit = 1 if ckout == "yes" else 0
    ckout_offset = ckout_bit << 6

    if target in targets_2:
        if oscillator == "external":
            return 0xFF & ~ckout_offset
        elif oscillator == "external_clock":
            return 0xE0 & ~ckout_offset
        else:
            if f_cpu == "8000000L":
                return 0xE2 & ~ckout_offset
            else:
                return 0x62 & ~ckout_offset

    else:
        sys.stderr.write("Error: Couldn't calculate lfuse for %s\n" % target)
        env.Exit(1)


def get_hfuse(target, uart, oscillator, bod, eesave, jtagen):
    targets_1 = (
        "atmega2561",
        "atmega2560",
        "atmega1284",
        "atmega1284p",
        "atmega1281",
        "atmega1280",
        "atmega644a",
        "atmega644p",
        "atmega640",
        "atmega324a",
        "atmega324p",
        "atmega324pa",
        "atmega324pb",
        "at90can128",
        "at90can64",
        "at90can32",
    )

    eesave_bit = 1 if eesave == "yes" else 0
    eesave_offset = eesave_bit << 3
    ckopt_bit = 1 if oscillator == "external" else 0
    ckopt_offset = ckopt_bit << 4
    jtagen_bit = 1 if jtagen == "yes" else 0
    jtagen_offset = jtagen_bit << 6

    if target in targets_1:
        if uart == "no_bootloader":
            return 0xDF & ~jtagen_offset & ~eesave_offset
        else:
            return 0xDE & ~jtagen_offset & ~eesave_offset

    else:
        sys.stderr.write("Error: Couldn't calculate hfuse for %s\n" % target)
        env.Exit(1)


def get_efuse(target, uart, bod, cfd):

    targets_5 = ("at90can128", "at90can64", "at90can32")

    cfd_bit = 1 if cfd == "yes" else 0
    cfd_offset = cfd_bit << 3

    if target in targets_5:
        if bod == "4.1v":
            return 0xFD
        elif bod == "4.0v":
            return 0xFB
        elif bod == "3.9v":
            return 0xF9
        elif bod == "3.8v":
            return 0xF7
        elif bod == "2.7v":
            return 0xF5
        elif bod == "2.6v":
            return 0xF3
        elif bod == "2.5v":
            return 0xF1
        else:
            return 0xFF

    else:
        sys.stderr.write("Error: Couldn't calculate efuse for %s\n" % target)
        env.Exit(1)


def get_lock_bits(target):
    return "0x0f"


board = env.BoardConfig()
platform = env.PioPlatform()
core = board.get("build.core", "")

target = (
    board.get("build.mcu").lower()
    if board.get("build.mcu", "")
    else env.subst("$BOARD").lower()
)

fuses_section = "fuses"
if "bootloader" in COMMAND_LINE_TARGETS:
    fuses_section = "bootloader"

lfuse = board.get("%s.lfuse" % fuses_section, "")
hfuse = board.get("%s.hfuse" % fuses_section, "")
efuse = board.get("%s.efuse" % fuses_section, "")
lock = board.get("%s.lock_bits" % fuses_section, get_lock_bits(target))
if "bootloader" in COMMAND_LINE_TARGETS:
    # A special case for unlocking chip to burn a new bootloader
    lock = board.get("%s.unlock_bits" % fuses_section, "0x3F")

if (not lfuse or not hfuse) and core not in (
    "MiniCore",
    "MegaCore",
    "MightyCore",
    "MajorCore",
    "MicroCore",
):
    sys.stderr.write(
        "Error: Dynamic fuses generation for %s is not supported."
        " Please specify fuses in platformio.ini\n" % target
    )
    env.Exit(1)

if core in ("MiniCore", "MegaCore", "MightyCore", "MajorCore", "MicroCore"):
    f_cpu = board.get("build.f_cpu", "16000000L").upper()
    oscillator = board.get("hardware.oscillator", "external").lower()
    bod = board.get("hardware.bod", "2.7v").lower()
    uart = board.get("hardware.uart", "uart0").lower()
    eesave = board.get("hardware.eesave", "yes").lower()
    jtagen = board.get("hardware.jtagen", "no").lower()
    ckout = board.get("hardware.ckout", "no").lower()
    cfd = board.get("hardware.cfd", "no").lower()

    print("\nTARGET CONFIGURATION:")
    print("---------------------")
    print("Target = %s" % target)
    print("Clock speed = %s" % f_cpu)
    print("Oscillator = %s" % oscillator)
    print("BOD level = %s" % bod)
    print("Save EEPROM = %s" % eesave)

    if target not in ("attiny13", "attiny13a"):
        print("UART port = %s" % uart)

    if target not in (
        "atmega8535",
        "atmega8515",
        "atmega128",
        "atmega64",
        "atmega32",
        "atmega16",
        "atmega8",
        "attiny13",
        "attiny13a",
    ):
        print("Clock output = %s" % ckout)

    if target in (
        "atmega2561",
        "atmega2560",
        "atmega1284",
        "atmega1284p",
        "atmega1281",
        "atmega1280",
        "atmega644a",
        "atmega644p",
        "atmega640",
        "atmega324a",
        "atmega324p",
        "atmega324pa",
        "atmega324pb",
        "at90can128",
        "at90can64",
        "at90can32",
        "atmega164a",
        "atmega164p",
        "atmega162",
        "atmega128",
        "atmega64",
        "atmega32",
    ):
        print("JTAG enable = %s" % jtagen)

    if target in ("atmega324pb", "atmega328pb"):
        print("CFD enable = %s" % cfd)

    print("---------------------")

    lfuse = lfuse or hex(get_lfuse(target, f_cpu, oscillator, bod, eesave, ckout))
    hfuse = hfuse or hex(get_hfuse(target, uart, oscillator, bod, eesave, jtagen))
    efuse = efuse or get_efuse(target, uart, bod, cfd)

env.Replace(
    FUSESUPLOADER="avrdude",
    FUSESUPLOADERFLAGS=[
        "-p",
        "$BOARD_MCU",
        "-C",
        '"%s"'
        % join(env.PioPlatform().get_package_dir("tool-avrdude") or "", "avrdude.conf"),
    ],
    FUSESFLAGS=[
        "-Ulock:w:%s:m" % lock,
        "-Uhfuse:w:%s:m" % hfuse,
        "-Ulfuse:w:%s:m" % lfuse,
    ],
    SETFUSESCMD="$FUSESUPLOADER $FUSESUPLOADERFLAGS $UPLOAD_FLAGS $FUSESFLAGS",
)

env.Append(FUSESUPLOADERFLAGS=["-e"])

if env.subst("$UPLOAD_PROTOCOL") != "custom":
    env.Append(FUSESUPLOADERFLAGS=["-c", "$UPLOAD_PROTOCOL"])
else:
    print(
        "Warning: The `custom` upload protocol is used! The upload and fuse flags may "
        "conflict!\nMore information: "
        "https://docs.platformio.org/en/latest/platforms/atmelavr.html"
        "#overriding-default-fuses-command\n"
    )

if efuse:
    efuse = efuse if isinstance(efuse, str) else hex(efuse)
    env.Append(FUSESFLAGS=["-Uefuse:w:%s:m" % efuse])

print(
    "\nSelected fuses: [lfuse = %s, hfuse = %s%s]"
    % (lfuse, hfuse, ", efuse = %s" % efuse if efuse else "")
)

fuses_action = env.VerboseAction("$SETFUSESCMD", "Setting fuses")

Return("fuses_action")
