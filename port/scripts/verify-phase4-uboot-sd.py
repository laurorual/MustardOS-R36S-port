#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Audit a bare-metal SD monitor; never execute the ELF or a boot command."""
from pathlib import Path
import hashlib
import json
import re
import runpy
import struct
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elf_symbols(path):
    data = path.read_bytes()
    assert data[:7] == b'\x7fELF\x02\x01\x01', 'ELF64 LE required'
    assert struct.unpack_from('<HH', data, 16) == (2, 183), 'bare-metal AArch64 ET_EXEC required'
    phoff, = struct.unpack_from('<Q', data, 32)
    phsize, phnum = struct.unpack_from('<HH', data, 54)
    assert phsize == 56 and phoff+phsize*phnum <= len(data)
    for index in range(phnum):
        kind, = struct.unpack_from('<I', data, phoff+index*phsize)
        assert kind not in [2, 3], 'unexpected dynamic linker/interpreter'
    shoff, = struct.unpack_from('<Q', data, 40)
    shsize, shnum = struct.unpack_from('<HH', data, 58)
    assert shsize == 64 and shoff+shsize*shnum <= len(data)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, shoff+i*shsize) for i in range(shnum)]
    symbols = {}
    environment = []
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        assert section[9] == 24 and section[4]+section[5] <= len(data)
        strings = sections[section[6]]
        names = data[strings[4]:strings[4]+strings[5]]
        for offset in range(section[4], section[4]+section[5], 24):
            name_offset, info, _, ndx, value, size = struct.unpack_from('<IBBHQQ', data, offset)
            name = names[name_offset:].split(b'\0', 1)[0].decode()
            if not ndx:
                continue
            symbols[name] = {'value': value, 'size': size, 'info': info}
            if name == 'default_environment' and info >> 4 == 1:
                target = sections[ndx]
                start = target[4]+value-target[3]
                assert target[4] <= start and start+size <= target[4]+target[5]
                environment.append(data[start:start+size])
    assert len(environment) == 1, 'one global default_environment required'
    assert struct.unpack_from('<Q', data, 24)[0] == 0x00200000, 'unexpected entry point'
    return symbols, environment[0]


def verify(stage):
    repo = Path(__file__).resolve().parents[2]
    record = json.loads((stage/'inputs.json').read_text())
    diagnostic = record.get('profile','monitor') in ['linux-diagnostic','ext4-diagnostic']
    ext4_diagnostic = record.get('profile') == 'ext4-diagnostic'
    expected_delay = '3' if diagnostic else '-1'
    assert (stage/'build.exit').read_text().strip() == '0'
    for name, digest in record['port_inputs'].items():
        assert sha(repo/name) == digest, name
    for name, digest in record['source_files'].items():
        assert sha(stage/'source'/name) == digest, name
    output = stage/'output'
    config = dict(re.findall(r'^(CONFIG_\w+)=(.*)$', (output/'.config').read_text(), re.M))
    assert config['CONFIG_ENV_IS_NOWHERE'] == 'y'
    assert config['CONFIG_BOOTDELAY'] == expected_delay
    assert config['CONFIG_PANIC_HANG'] == 'y'
    assert int(config['CONFIG_ROCKCHIP_BOOT_MODE_REG'], 0) == 0
    assert config['CONFIG_USING_KERNEL_DTB'] == 'y'
    assert config['CONFIG_SYSMEM'] == 'y' and config['CONFIG_BIDRAM'] == 'y'
    assert config['CONFIG_DEFAULT_DEVICE_TREE'] == '"odroidgoa"'
    disabled = ['ENV_IS_IN_MMC', 'CMD_SAVEENV', 'CMD_RKSFC', 'CMD_SF', 'CMD_SPI', 'RKFLASH',
                'RKSFC_NOR', 'RKSFC_NAND', 'CMD_ROCKUSB', 'USB_GADGET_DOWNLOAD', 'OPTEE_CLIENT',
                'DM_CHARGE_DISPLAY', 'CMD_CHARGE_DISPLAY', 'CMD_ODROID_HWREV', 'CMD_ODROID_TEST',
                'CMD_ODROID_ADC', 'CMD_ODROID_BATTERY', 'CMD_ODROID_CFGLOAD', 'CMD_GPT',
                'CMD_EXT4_WRITE', 'FAT_WRITE', 'USE_PREBOOT', 'ROCKCHIP_VENDOR_PARTITION',
                'CMD_GO', 'TEST_ROCKCHIP']
    for name in disabled:
        assert config.get('CONFIG_'+name) != 'y', name
    # Check effective preprocessor results too: the base board previously
    # overrode Kconfig's environment offset and bootcommand in its header.
    macros = dict(re.findall(r'^#define (CONFIG_\w+)\s+(.*)$', (output/'u-boot.cfg').read_text(), re.M))
    assert macros['CONFIG_BOOTDELAY'].strip('() ') == expected_delay
    for name in ['CONFIG_PREBOOT', 'CONFIG_SUPPORT_EMMC_RPMB', 'CONFIG_USB_FUNCTION_MASS_STORAGE']:
        assert name not in macros, name
    symbols, raw_env = elf_symbols(output/'u-boot')
    assert raw_env.endswith(b'\0\0')
    env = {}
    for item in raw_env.split(b'\0'):
        if not item:
            continue
        key, value = item.decode().split('=', 1)
        assert key not in env, ('duplicate compiled environment key', key)
        env[key] = value
    assert env['devtype'] == 'mmc' and env['devnum'] == '1'
    assert env['hwrev'] == 'rg351mp' and env['lcd_rotate'] == '0'
    assert env['fdt_addr_r'] == '0x01e00000'
    assert 'bootdelay' not in env or int(env['bootdelay']) == int(expected_delay)
    assert all(name not in env for name in ['preboot', 'altbootcmd', 'failbootcmd', 'spi_upgrade_from_sd'])
    expected_command = (
        'if mmc dev 1; then '
        'if fatload mmc 1:1 0x02000000 Image 0x04000000; then '
        'if fatload mmc 1:1 0x01f00000 rk3326-muos-r35s-panel0.dtb 0x00040000; then '
        'booti 0x02000000 - 0x01f00000; '
        'else echo Linux DTB load failed; fi; '
        'else echo Image load failed; fi; '
        'else echo SD probe failed; fi')
    if diagnostic:
        assert env['bootcmd'] == 'muos_linux_diag'
        if ext4_diagnostic:
            expected_args=('console=ttyFIQ0,115200n8 console=tty0 '
                           'root=PARTUUID=4d554432-02 rootfstype=ext4 rootwait ro '
                           'init=/sbin/muos-ext4-diag loglevel=7 consoleblank=0 '
                           'vt.global_cursor_default=0 panic=0 oops=panic muos_diag=MUOS-R35S-EXT4-P4-B01')
        else:
            expected_args=('console=ttyFIQ0,115200n8 console=tty0 rdinit=/init '
                                  'loglevel=7 ignore_loglevel consoleblank=0 vt.global_cursor_default=0 '
                                  'panic=0 oops=panic muos_diag=MUOS-R35S-LINUX-P4-A01')
        assert env['bootargs']==expected_args
        assert env['fdt_high'] == env['initrd_high'] == '0xffffffffffffffff'
        assert 'CONFIG_SUPPORT_RAW_INITRD' in macros and 'CONFIG_SYS_BOOT_RAMDISK_HIGH' in macros
        asset_path=Path(record['diagnostic_assets_manifest'])
        assert sha(asset_path) == record['diagnostic_assets_manifest_sha256']
        assets=json.loads(asset_path.read_text())
        assert assets['userspace_qemu_checked']
        for item in assets['assets'].values():
            assert sha(Path(item['path'])) == item['sha256']
        assert assets['assets']['Image']['bytes']+1 < 0xec0000
        if ext4_diagnostic:
            assert assets['root_partuuid']=='4d554432-02'
            assert sha(Path(assets['rootfs']['path']))==assets['rootfs']['sha256']
            assert assets['frontend_enabled'] is False
        else:
            assert assets['assets']['initramfs.cpio.gz']['bytes']+1 < 0x800000
        assert assets['assets']['rk3326-muos-r35s-panel0.dtb']['bytes']+0x10000 < 0x40000
        generated=(stage/'source/include/configs/muos-r35s-linux-assets.h').read_text()
        names=[('Image','IMAGE'),('rk3326-muos-r35s-panel0.dtb','LINUX_FDT')]
        if not ext4_diagnostic:names.append(('initramfs.cpio.gz','INITRD'))
        for asset,macro in names:
            item=assets['assets'][asset]
            assert f'#define MUOS_{macro}_BYTES {item["bytes"]}UL' in generated
            digest=','.join('0x'+item['sha256'][i:i+2] for i in range(0,64,2))
            assert f'#define MUOS_{macro}_SHA256 {{{digest}}}' in generated
        if ext4_diagnostic:assert 'MUOS_INITRD_' not in generated
    else:
        assert env['bootcmd'] == expected_command, env['bootcmd']
        assert 'rootfstype=ext4 rootwait ro init=/bin/sh' in env['bootargs']
        assert 'root=/dev/mmcblk0p2' in env['bootargs']
    commands = sorted(name.split('_u_boot_list_2_cmd_2_', 1)[1] for name in symbols if '_u_boot_list_2_cmd_2_' in name)
    assert 'booti' in commands and 'fatload' in commands and 'mmc' in commands
    if diagnostic:
        assert 'muos_linux_diag' in commands and 'sha256_csum_wd' in symbols
    assert not set(commands) & {'saveenv', 'rksfc', 'sf', 'sspi', 'rockusb', 'odroidtest', 'hwrev', 'cfgload', 'gpt', 'fatwrite', 'ext4write', 'rbrom', 'go', 'rktest'}
    forbidden = ['board_odroid_recovery', 'board_check_recovery', 'recovery_check_mandatory_files',
                 'env_mmc_load', 'env_mmc_save', 'do_saveenv', 'do_hwrev', 'do_odroidtest',
                 'rksfc_scan_namespace', 'do_programkey', 'init_rpmb', 'do_authenticatedwrite',
                 'rockchip_get_boot_mode', 'do_reboot_brom']
    assert not set(forbidden) & symbols.keys(), set(forbidden) & symbols.keys()
    assert 'env_nowhere_init' in symbols
    for name in ['board_sysmem_reserve', 'board_lmb_reserve', 'muos_reserve_control_fdt', 'muos_reserve_bootm_fdt']:
        assert symbols[name]['info'] >> 4 == 1, ('strong memory hook missing', name)
    # Dynamic fixture uses the actual pinned allocator and adapter sources.
    memory = json.loads((stage/'memory-audit/report.json').read_text())
    assert memory['passed'] and memory['ubsan_passed'] and not memory['hardware_tested']
    for name, digest in memory['source_sha256'].items():
        assert sha(stage/'source'/name) == digest, name
    for name, digest in memory['port_inputs'].items():
        assert sha(repo/name) == digest, name
    board_source = (stage/'source/arch/arm/mach-rockchip/board.c').read_text()
    loader = board_source[board_source.index('int init_kernel_dtb(void)'):]
    assert loader.index('muos_reserve_control_fdt()') < loader.index('fatload mmc')
    native_boot_hook = board_source[board_source.index('void board_lmb_reserve(struct lmb *lmb)'):]
    assert 'muos_reserve_bootm_fdt(lmb);' in native_boot_hook.split('\n}', 1)[0]
    binary = (output/'u-boot.bin').read_bytes()
    for text in [b'spi_recovery.img', b'rksfc write', b'mmc erase 0x1 0x7FFF', b'spi_upgrade_from_sd']:
        assert text not in binary, text
    assert (b'Linux diagnostic: U-Boot reached' if diagnostic else b'SD monitor: U-Boot reached') in binary
    assert 'lcd_init' in symbols and memory['visual_monitor_gates_and_formatted_lines_mocked']
    link_map = (output/'u-boot.map').read_text()
    for name in ['odroidgoa_recovery.o', 'odroidgoa_power.o', 'odroidgoa_status.o', 'env/mmc.o']:
        assert name not in link_map, name
    assert binary == (output/'u-boot-nodtb.bin').read_bytes()+(output/'u-boot.dtb').read_bytes()
    assert len(binary) <= 0x00100000-2048, 'exceeds one-MiB loader copy minus its header'
    properties = runpy.run_path(str(Path(__file__).with_name('verify-phase4-dtb.py')))['properties']
    for path in [output/'u-boot.dtb', stage/'rk3326-muos-r35s-panel0-uboot.dtb']:
        tree, _ = properties(path)
        delay = tree.get(('/config', 'bootdelay'))
        assert delay is None or delay == (b'\x00\x00\x00\x03' if diagnostic else b'\xff\xff\xff\xff'), path
    panel = json.loads((stage/'audit/display.json').read_text())
    assert panel['passed'] and not panel['boot_tested']
    (stage/'audit/default-environment.json').write_text(json.dumps(env, indent=2)+'\n')
    (stage/'audit/commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    artifacts = ['u-boot', 'u-boot.bin', 'u-boot-nodtb.bin', 'u-boot.dtb', 'u-boot.cfg', 'u-boot.map', 'System.map', '.config']
    return {'scope': 'static host audit of the bare-metal U-Boot SD '+('Linux diagnostic' if diagnostic else 'monitor')+' probe', 'passed': True,
            'inputs': record, 'elf': 'AArch64 ET_EXEC, entry 0x200000, no Linux interpreter/dynamic linker',
            'output_sha256': {name: sha(output/name) for name in artifacts},
            'u_boot_bin_bytes': len(binary), 'display': panel,
            'compiled_environment_checked': True, 'command_table_checked': True,
            'control_fdt_reserved_in_sysmem_and_bootm_lmb': True,
            'visual_monitor_prepared': True, 'visual_monitor_hardware_tested': False,
            'native_allocator_host_fixture': memory,
            'identified_legacy_recovery_and_persistent_env_paths_absent': True,
            'automatic_boot': diagnostic, 'power_battery_policy_integrated': False,
            'panic_hangs_without_automatic_reset': True,
            'interactive_mmc_command_still_has_write_and_erase': True,
            'complete_boot_call_graph_proven': False,
            'vendor_loader_trust_packaged': False, 'media_written': False, 'boot_tested': False,
            'audit_port_inputs': {str(p.relative_to(repo)): sha(p) for p in
                                  [Path(__file__), Path(__file__).with_name('audit-phase4-uboot-sd.sh'),
                                   Path(__file__).with_name('verify-phase4-uboot-panel.py')]}}


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1])), indent=2))
