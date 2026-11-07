# Consulta pronta sobre os termos do Mali r13p0

**Adiada por decisão do usuário em 25/10/2026.** O desenvolvimento prossegue
com candidata privada, mantendo a licença como pendência. Esta consulta não
precisa ser encaminhada agora. O [registro central](../../port/packaging/pending-licenses.json)
alimenta o Markdown consolidado solicitado para o **fim do projeto**;
nenhuma mensagem foi enviada. A autorização do proprietário para os ensaios
não fornece os termos ausentes do distribuidor.

Ainda não enviada. Destino: suporte/distribuidor Hardkernel ou o responsável
indicado por ele. Não solicitar que terceiros licenciem código de que não
detenham os direitos.

## Texto em inglês

Subject: Applicable license and redistribution terms for RK3326 r13p0 Mali ZIP

Hello,

I am developing an AArch64 firmware for an RK3326 handheld with a Mali-G31
GPU. I found the following package on the Hardkernel download server:

https://dn.odroid.com/RK3326/ODROID-GO-Advance/rk3326_r13p0_gbm_with_vulkan_and_cl.zip

ZIP SHA256:
`ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9`

The AArch64 member is
`libmali.so_rk3326_gbm_arm64_r13p0_with_vulkan_and_cl`, SHA256:
`2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea`.

The ZIP contains two binaries and no license text. Could you please identify
the license/EULA that applies to this exact package and provide its text
or an authoritative link? In particular:

1. Does it permit private use and redistribution in a Linux firmware for
   RK3326/Mali-G31 devices made by other manufacturers, such as the R35S?
2. Which copyright notices, license copies or end-user terms must accompany
   a redistributed binary?
3. Are packaging changes such as adding a SONAME or stripping symbols
   permitted? We can keep the original binary unchanged if required.
4. If Hardkernel cannot confirm the applicable terms, which ARM/Rockchip
   contact or release should we use instead?

The application sources are GPLv3 and the driver is a separate dynamically
loaded library; we need to assess the complete distribution before publishing
anything. We are not requesting that this proprietary driver be relicensed
as GPL or assuming that another libmali package's EULA covers it.

Thank you.

## Critério para encerrar a pendência

Guardar o texto/link da licença aplicável com a identidade exata do pacote,
origem e condições, sem credenciais ou dados pessoais. Uma indicação genérica
de “nonfree” ou um EULA que acompanha outro binário não fecha esta consulta.
Uma resposta sobre a licença do driver também não substitui a análise do
conjunto efetivamente publicado.
