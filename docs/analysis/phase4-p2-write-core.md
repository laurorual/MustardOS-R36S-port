# C87 parcial — núcleo limitado à p2, preparado offline

Preparado em **04/11/2026**. O usuário solicitou encerrar a rodada com apenas
3% do limite restante. Esta etapa entrega o primitivo de escrita e testes de
falhas; **não conclui o backend físico**, não habilita gravação de C79 e não
altera kernelRO/regra C83. Nenhuma escrita no cartão, seed, fence ou boot.

`port/scripts/phase4_p2_write_core.py` não abre dispositivos. Recebe descritores
e callbacks do futuro controller e fixa o único intervalo de destino em
128MiB..640MiB,512MiB de p2. Não recebe offset/tamanho arbitrários. Verifica
hash da fonte e p2 atual, regiões protegidas, registra intenção durável antes
do primeiro pwrite, escreve blocos1MiB sem completar/repetir escrita curta,
faz fsync e relê fonte/destino. Nenhum rollback automático.

Restauração de RO pertence ao finally; falha de proteção impede recibo de
conclusão. Callback de restauração deverá operar só sobre aliases cuja
identidade/propriedade o controller realmente confirmou, inclusive se o
preflight falhar. A conclusão não autoriza entregar a mídia ao console:
fence C84 de possível boot é uma etapa distinta, ainda necessária. Erro de
recibo final preserva intenção de possível escrita e exige inspeção.

Testes usam descritores virtuais com callbacks, sem arquivo de cartão/ext4,
rede ou dispositivo físico. Cobrem os512MiB e limites exatos, hash/fonte
alterados, preflight, persistência da intenção, escrita curta/erro sem retry,
fsync, readback, regiões protegidas, proteção RO e argumentos inválidos.
Não qualificam kernel, controlador, queda elétrica, fsck ou controller real.

Survey somente leitura confirmou Deck Jupiter/IP192.168.15.13, desmontado,
sem snapshots e quatro aliasesRO. Kernel observado:
`7.2.7-valve2-2-neptune-72-g31504582a073`. Fontes locais Linux4.4 e
[upstream ioctl.c](https://github.com/torvalds/linux/blob/master/block/ioctl.c)
foram consultados para planejar a transição RO, junto ao
[contrato de leitura RO](https://github.com/torvalds/linux/blob/master/include/linux/blkdev.h).
Isso não valida o comportamento do kernel Valve instalado. Nenhum código GPL
foi copiado; implementação própria MIT. Não executar BLKROSET=0 por inferência.

Retomada: implementar controller físico com verificação de descritores,
CID/geometria/MBR, ausência de consumidores, backups independentes C82/C86,
imagem provisionada/recuperação validada, journal exclusivo e transição RO
planejada e testada. Vincular fsync/readback/cache/proteções e fence de boot.
Não implantar este primitivo sozinho no Deck nem reutilizar restore C20.
Manter cartão no Deck, backups/SDK/imagens e original32 intactos.

16casos passaram em `build/phase4/p2-writer/checks.nxrw8_jj`. Prova pública
`dist/phase4/p2-write-core`: fontes, testes virtuais e resumo; nenhum payload
privado ou imagem. Não houve deploy do writer nem transição de proteção.
