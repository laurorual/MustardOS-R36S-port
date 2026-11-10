# C70 — imagem privada completa para o Panel 0

Concluído em 03/11/2026, sem contato com console, cartões ou Steam Deck.
O [compositor](../../port/scripts/compose-phase4-card-image.py) integrou a
ext4 C69 à cadeia de boot B01 e aos mesmos kernel/DTB aprovados no aparelho.
Nenhum desses componentes foi recompilado. A imagem raw privada tem 640 MiB,
SHA256 `f82f9ddd56b29765a4d852c6ef7dce0a0a6678915a4426d3c706155b77293671`.

| Região | Início | Tamanho/contrato |
| --- | --- | --- |
| MBR | setor 0 | assinatura 4d554432, duas partições |
| idbloader | setor 64 | payload B01 fixado |
| U-Boot | setor 16384 | 4 MiB, ambiente persistente desabilitado |
| trust | setor 24576 | 4 MiB, payload B01 fixado |
| p1 | 16 MiB | FAT32, 100 MiB, MUOSDIAG |
| p2 | 128 MiB | ext4 C69, 512 MiB, PARTUUID 4d554432-02 |

Foi mantida a inicialização `ro init=/sbin/muos-ext4-diag`. Esse bootstrap
da raiz atual verifica mídia/modelo/kernel/contrato e entra no BusyBox/C07.
O marcador FAT continua B01 por exigência dos diagnósticos existentes.
Não foram adicionados scripts de startup FAT, initramfs ou terceira partição.
As constantes de tamanho e SHA256 de Image/DTB embutidas no U-Boot foram
comparadas com os arquivos efetivamente copiados. A aprovação B01 é evidência
dos componentes anteriores; a combinação C70 inteira ainda não foi iniciada.

O [verificador](../../port/scripts/phase4_card_image.py) releu MBR canônico,
cinco regiões completas e todos os intervalos restantes, que devem conter
somente zeros. As seis folhas do FAT foram extraídas da imagem final e
comparadas byte a byte com os assets. Ambas as partições foram extraídas
sem loop device/mount e seus hashes comparados às fontes. O FAT novo passou
em fsck; a ext4 reutiliza o fsck0 C69 após releitura de hash idêntico. O gzip
privado também foi descomprimido e conferido contra o hash da imagem raw.

Passaram [27 casos de guarda](../../port/scripts/check-phase4-card-image.py):
imagem válida/restaurada; MBR, assinatura, entradas e trailer alterados;
terceira partição; bytes em intervalos vazios; corrupção de cada região;
truncamento/tamanho excessivo; symlink/hardlink; regiões extras, ausentes,
deslocadas, sobrepostas, negativas e digest inválido. São fixtures sintéticas
esparsas de arquivo regular, sem acessar dispositivos de bloco.

A primeira tentativa `image.co2qhsf9` revelou que comparar `stat_result`
inteiro também compara atime alterado pela leitura. A guarda foi corrigida
para identidade, tamanho, mtime, ctime e nlink, com O_NOFOLLOW no open. A
segunda `image.aby0k5zj` chegou à extração, mas tentou e2fsck no container de
mídia, que não o contém. A candidata final reutiliza o fsck C69 em vez de
instalar ferramentas ou repetir teste de bytes já aprovados. Nenhuma dessas
tentativas foi publicada como candidata aprovada ou enviada ao aparelho.

Stage aprovado: `build/phase4/card-image/image.ce6thxbu`. Checks:
`build/phase4/card-image/checks.o9c6w_ot`. Fontes e recibos ficam em
`dist/phase4/card-image`; imagem, gzip e payloads permanecem em build privado.
O SDK, raiz C69 e artefatos B01 permanecem intactos.

Esta é uma imagem factory: contador zero, sem credenciais Wi-Fi, seed RNG,
host keys, ROMs, cores libretro, saves ou volume userdata. UI, sessão e
preferências automáticas continuam desligadas. É necessário provisionamento
antes de um boot supervisionado com SSH. Não é atualização que preserve os
dados atuais do cartão, nem há writer habilitado neste incremento. Licenças
pendentes da cadeia de boot/GPU continuam impedindo tratar o payload privado
como release redistribuível. Outros painéis, boot da combinação, resize,
reprodutibilidade binária e frontend permanente continuam sem qualificação.
