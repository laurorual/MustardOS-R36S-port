# Request: redistribution terms for Hardkernel's RK3326 Mali r13p0 package

Status: revised 2026-11-14 (decision 2 = (a)); sent by the user, not by
the agent. Tracked in
[pending-licenses.json](../../../port/packaging/pending-licenses.json)
(`hardkernel-mali-r13p0-rk3326`).

**Where to send it:**
- Email: `odroid@hardkernel.com`, the only address Hardkernel publishes
  (hardkernel.com/contact-us). The page says it doesn't do *technical*
  support by email, but this is a licensing/business question.
- If there's no answer in ~2 weeks: post the same text on the ODROID
  forum (forum.odroid.com, ODROID-GO Advance board), where Hardkernel
  staff answer publicly. A public answer is also easier to cite.

Fill in the two placeholders before sending. Don't attach the binary.

---

**Subject:** Redistribution terms for rk3326_r13p0_gbm_with_vulkan_and_cl.zip (Mali-G31 userspace)

Hello Hardkernel team,

I'm working on an open-source, unofficial port of muOS (a handheld
gaming frontend) to RK3326 handhelds, the R35S/R36S. The port uses the
Rockchip 4.4 BSP kernel, whose Mali kbase is r13p0. The only matching
AArch64 userspace driver I could find is the one on your download server:

- https://dn.odroid.com/RK3326/ODROID-GO-Advance/rk3326_r13p0_gbm_with_vulkan_and_cl.zip
  (SHA256 `ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9`)
- member `libmali.so_rk3326_gbm_arm64_r13p0_with_vulkan_and_cl`
  (SHA256 `2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea`)

The archive contains no license text, so before I publish anything I'd
like to know the terms that apply to it:

1. Which license or EULA covers this package? A copy or a link would be
   great.
2. Does it allow redistributing this library inside a free,
   publicly downloadable firmware image for RK3326/Mali-G31 devices made
   by other manufacturers (the R35S/R36S)?
3. If so, what must go with it (copyright notice, license text, EULA)?
4. My build currently makes two packaging changes: it sets the SONAME to
   `libmali.so.1` and strips symbols. Is that allowed, or must the file
   ship byte-identical? I can ship it unmodified if required.
5. If the terms aren't Hardkernel's to give, could you point me to the
   right contact at Rockchip or Arm?

The library is a separate file loaded at run time, and I'm not asking for
it to be relicensed. If redistribution isn't allowed, I'll ship the
firmware without it and tell users where to download it themselves.

Project page: [GitHub URL]

Thank you for your time,
[Your name]

---

## When it's answered

Record in `pending-licenses.json`: who answered, the date, the license
text or link, and the conditions, tied to the exact file hashes above.
Keep no personal data or credentials there. A generic "it's proprietary"
or another package's EULA doesn't close this item.
