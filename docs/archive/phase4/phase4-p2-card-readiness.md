# C90 — claim exclusivo e transição RO no MMC real, sem payload

Em **04/11/2026**, o test128 no Steam Deck Jupiter/kernel7.2.7-valve2 passou
o ensaio explícito da proteção de bloco. O controlador foi o mesmo C87
qualificado em loop, com adapter C89 fixo ao CID/geometria/aliases do cartão.
O original32 permanece fora do fluxo.

O helper finito `phase4-p2-card-readiness.py check` não chama apply/write_p2,
write/pwrite/writev, clonagem de imagem, mount, init, reboot ou RNG. Abre
descritores de controle somente após identidade/guardas C82/C86; confere RO1
nos quatro aliases e hash p2/MBR/prefixo. Journal exclusivo e fsync antecedem
o SETRO0 de whole/p2. P1/p3 continuam RO1. Abre claim O_RDWR|O_EXCL no whole,
confere F_GETFL e mantém apenas leituras. Restaura RO1 pelos FDs verificados,
fecha o claim e repete leitura via claim RO/caches sincronizados.

As três leituras integrais512MiB coincidiram com a referência C86/raiz0755,
contador72. MBR e prefixo16MiB coincidiram nas três fases. Não houve
write-intent ou escrita de payload; o journal tem só intenção de transição
de proteção e conclusão. Nenhum seed, chave, candidata em mídia ou fence de
possível boot foi criado. Não houve hash integral da p3 nem qualificação de
gravação/queda elétrica/bootC79. A p3 permaneceu kernelRO durante o claimRW.

17casos virtuais de transição/falhas/bootstrap/contrato sem payload passaram;
19casos de recibo/guardas do coletor passaram. O usuário executou sudo local
no Deck (SSH sem sudo sem senha) e confirmou READINESS COMPLETE. Os recibos e
journals foram copiados com fsync, código/hashes/proveniência conferidos e o
estado real relido: cartão desmontado, quatro aliasesRO1, regra C83 intacta e
sem snapshot de código root pendente. A transição do MMC real agora está
qualificada para esse kernel/leitor/cartão; a escrita física continua separada.

Privados `build/phase4/card-readiness`: `package.dfrpf2_2`,
`checks.slu36_9j`, `copy.vd5atohm`; pointers latest-package/latest-checks/
latest-complete/latest-transport-checks. Deck resultado
`/var/tmp/muos-r35s-c90-readiness.5u4bjdhb`. Prova redigida card-readiness só
inclui fontes/casos/resumo, sem contextos, hashes privados, imagens ou chaves.
Original32, SDK, referências e backups C82/C83/C86 preservados.
