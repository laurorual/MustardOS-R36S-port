# C112 — assets residentes e preparação da ROM interna

Data:07/11/2026. Retoma o lote interrompido antes de qualquer instalação C112.
O usuário pediu explicitamente que a ROM também passasse a ter origem interna.
O console foi encontrado no boot82/C07 pronto; nova observação confere178
hashes, layout e quatro arquivos estáveis de identidade. Não reescreve UUID81,
não pede outro reboot e não altera C105/C109/C111 históricos.

O pacote adiciona13 arquivos em `/usr/libexec/muos-resident`,1.871.877bytes,
sem substituir os anteriores. Quatro assets exatos C109: runner, metadata,
libmuxmod diagnóstico C46 e probe ABI. MIT para código próprio, licença GPLv3
original do frontend incluída; sem recompilar frontend/provider/core ou copiar
subsystems de refs. Provas de origem e fontes anteriores permanecem preservadas.
O uso continua privado, sem autorização de redistribuição do firmware.

Acrescenta um utilitário MIT pequeno, `sync-path`, compilado AArch64/A35 pelo
SDK existente em container, PIE/relro/now/stack protector/Wall/Wextra/Werror.
Aceita até cinco caminhos absolutos de arquivos/diretórios root, sem symlink
final, em ext4/tmpfs; arquivos devem ter nlink1 e nenhum objeto pode ser gravável
por grupo/outros. Abre somente leitura e chama fsync, sem ler conteúdo.
Retorna64 na recusa e74 em falha de flush/close. BusyBox nativo oferece apenas
sync global, motivo desta adição. Não qualifica queda de energia.

`load.sh check` valida o pacote e dependências instaladas. `prepare` exige uma
cápsula RAM vazia: cria quatro inputs públicos localmente; um subprocesso num
namespace privado lê a ROM da p3, ro,noload/nosuid/nodev/noexec, valida shelf,
manifesto/modos/links/hash e copia para inputs/private.gb. Desmonta/remove o
mountpoint antes de voltar ao namespace global e delegar ao C111 original.
Assim, preserva o requisito GLOBAL de c25_media, sem relaxá-lo para ler a ROM.
O novo marcador resident identifica esse caminho depois de C111 completo.

A ROM ficará separada na p3: `MUOS/port-roms-v1/gb/private.gb`, com registro
privado e marcador próprios; não integra o pacote público, Git ou provas.
Sua importação é C113, precedida de backup lógico independente. Este pacote
não escreve na p3, não cria biblioteca geral e não abre UI.

52 casos locais passaram em `resident-assets/checks.obt45s39`: preparo/cópia
byte-exata, pacote/dependências/aliases/modos/hash/manifestos, sem repetição,
fases falhas, helper A35/QEMU fsync e transação real13folhas/rollback. Cinco
variantes negativas verificam boot/UUID novo, sem aproveitar registros antigos.
Guardas de mídia/namespace são callbacks na fixture; não acessa o cartão.

Pacote `package.2p14ff4n`; observação `observe.xx0kthce`; instalação
`install.0uvf0x6y` concluída no boot82:13folhas novas, check e recusa de
cápsula ocupada nativos0, fingerprint privado/infra/mountinfo preservados,
RAM removida/raizRO. Claim consumido; não redisparar apply. Prova sanitizada
`dist/phase4/resident-assets-installed`, omitindo os cinco ELFs e qualquer
ROM/seed/identidade privada. A instalação não importa ROM nem afirma aprovação
gráfica. Próximos C113 e integração completa usam o
mesmo boot82 após conferir integridade real. Nenhuma imagem completa criada.
