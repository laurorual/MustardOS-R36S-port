# Licence requests (M9 item 5)

Drafts the user sends; answers go into `port/packaging/pending-licenses.json`
and this file (date, who, what was allowed). The public image is published
only after explicit answers for every non-open component (decision 27).

| # | To | Where | Component | State |
|---|---|---|---|---|
| 1 | Hardkernel | odroid@hardkernel.com (copy: forum.odroid.com, ODROID-GO Advance board) | Mali-G31 r13p0 userspace | first request 2026-11-14, no answer; follow-up below |
| 2 | Exophase (DraStic) | drastic-ds.com forum (the author's only public contact found; confirm before sending) | DraStic r2.5.2.2 binary | to send |
| 3 | trngaje | GitHub issue on trngaje/advanced_drastic (and drastic_layout) | libadvdrastic.so, layout art | to send |
| 4 | steward-fu | GitHub (github.com/steward-fu), issue on his NDS repository | layout art (with trngaje) | to send |
| 5 | MustardOS team | GitHub Discussions/issue on MustardOS/internal, or their Discord | project name, bundled themes | to send if not sent (decision 12) |

Not permission questions (the port fixes them itself): the open-source
licences (GPL/Zlib/OFL: notices in `THIRD-PARTY.txt`, source bundle), the
non-commercial cores (Snes9x 2005, PicoDrive, FBNeo, MAME 2003-Plus: free
distribution allowed, no sale), the rkbin payloads (rkbin LICENSE).

## 1. Hardkernel (follow-up)

Subject: Follow-up: redistribution terms for the RK3326 Mali r13p0 userspace (rk3326_r13p0_gbm_with_vulkan_and_cl.zip)

> Hello Hardkernel team,
>
> On 14 November I asked about the terms for the Mali-G31 r13p0 userspace
> driver you publish for the ODROID-GO Advance
> (https://dn.odroid.com/RK3326/ODROID-GO-Advance/rk3326_r13p0_gbm_with_vulkan_and_cl.zip,
> sha256 ef1a18fa…d0ea of the archive). I am preparing a free, non-commercial
> firmware (an unofficial port of the open-source MustardOS frontend) for
> RK3326 handhelds (R36S/R35S), and would like to include this driver
> unmodified.
>
> Could you tell me:
> 1. which licence or EULA applies to these files;
> 2. whether they may be redistributed inside a free firmware image for
>    other RK3326 devices (not ODROID hardware);
> 3. which notices must accompany them;
> 4. whether stripping symbols or adjusting the SONAME links is allowed.
>
> If redistribution is not possible, a short "no" is also very helpful.
> Thank you very much.

## 2. Exophase (DraStic)

Subject: Permission to include DraStic in a free R36S/R35S firmware

> Hi Exophase,
>
> I am building a free, non-commercial firmware for the R36S/R35S
> handhelds (RK3326), an unofficial port of the open-source MustardOS
> frontend. DraStic r2.5.2.2 (aarch64) is by far the best NDS emulator on
> this hardware, and I would like to ship the unmodified binary in the
> image, credited to you, launched from the menu like other emulators
> (as dArkOS and other community firmwares do).
>
> May I redistribute it this way? Are there conditions you want (credit
> text, no modification, link to your site, non-commercial only)? If you
> prefer it not to be bundled, I will make the firmware download it on the
> user's request instead. Thank you for DraStic.

## 3. trngaje (advanced_drastic, drastic_layout)

Title: Licence for advanced_drastic and drastic_layout?

> Hi trngaje, thank you for advanced_drastic and the layouts.
>
> I am preparing a free, non-commercial firmware for the R36S/R35S
> (an unofficial MustardOS port) and would like to include libadvdrastic.so
> (built from d445a56) and the drastic_layout art (e8dc3eb), credited to
> you and steward-fu. The repositories have no licence file. Could you add
> one, or tell me under which terms they may be redistributed? Thank you!

## 4. steward-fu

Title: Permission for the DraStic layout art (drastic_layout)

> Hi steward-fu, the drastic_layout repository by trngaje credits your
> layout work. I would like to ship these layouts, credited, in a free,
> non-commercial R36S/R35S firmware (an unofficial MustardOS port). May I
> redistribute them, and under which terms? Thank you for your work.

## 5. MustardOS team

Title: Unofficial muOS port for R36S/R35S: name and bundled themes

> Hello MustardOS team,
>
> I have ported muOS to the RK3326 R36S/R35S (native AArch64, your
> frontend unmodified except for device patches published with the
> source, GPL-3.0). Before a public release I would like your OK on two
> points:
> 1. the name "muOS for R36S/R35S (unofficial port)", with a clear note
>    that it is not supported by the MustardOS team (support questions
>    go to the port's GitHub);
> 2. shipping the six bundled themes (MustardOS, C64, Dracula, GB Dark,
>    Orange, mubiOS) in the image; are they under the GPL with the
>    internal repository, or do some need their authors' permission?
>
> If you would prefer another name or no bundled themes, I will follow
> that. Thank you for muOS.
