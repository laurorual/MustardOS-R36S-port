# C87 — controlador p2 e qualificação no kernel do Deck

Em **04/11/2026**, o controlador foi qualificado em dispositivo loop criado
pelo próprio helper no Steam Deck Jupiter, kernel
`7.2.7-valve2-2-neptune-72-g31504582a073`. Isso qualifica IO de bloco e a
transição RO nesse kernel; não é ensaio de gravação da flash do test128,
boot da C79, recuperação após boot ou falha elétrica.

`phase4_p2_controller.py` mantém os descritores de controle dos quatro
aliases verificados. Antes de desbloquear, valida a fonte regular privada,
executa o validador de imagem, compara p2 atual e calcula hashes de todo o
complemento protegido. No cartão real, esse complemento inclui todo o
prefixo128MiB e toda a p3; não há amostragem. O alvo da fixture tem656MiB,
com p2 de512MiB no mesmo offset128MiB e p3 descartável de16MiB.

O journal exclusivo0400 recebe `unlock-intent` com fsync de arquivo e
diretório antes de SETRO0. O controlador fecha o claim somente leitura,
mantém a identidade/ausência de consumidores e reabre o mesmo dispositivo
com O_RDWR|O_EXCL. Esse intervalo é explícito: não é possível promover o
modo de acesso do descritor aberto. Só whole/p2 ficam graváveis; p1/p3
continuam RO. O primitivo C87 fixa todas as escritas em128..640MiB,
registra `write-intent`, recusa escrita curta sem completar/repetir e exige
fsync/readback. Finalmente reforça RO1 nos quatro descritores já verificados.
Uma falha em um deles não impede a tentativa nos demais. Não redescobre
dispositivos durante a recuperação de proteção.

Antes de publicar `complete`, sincroniza/invalida caches dos aliases,
reabre claim somente leitura e relê p2 e o complemento completo. Erro de
proteção, validação, intenção ou recibo não autoriza boot/rollback/repetição.
Um journal existente, inclusive parcial, é recusado. O fence C84 de possível
boot continua separado e necessário antes da entrega física da mídia.

O_EXCL não é tomado como prova suficiente contra descritores raw de outros
processos. A guarda examina `/proc/*/fd` além das guardas existentes de
namespace/mount/swap/holders. No Deck, três descritores do LocalSend em
`fuse.localsend.appimage` recusaram stat por root, embora o UID dono pudesse
lê-los. A correção não ignora FUSE nem infere tipo pelo nome: um filho curto
descarta grupos suplementares/UID/GID e consulta somente os metadados como
o dono estável do processo. UID/GID/starttime são conferidos antes/depois;
descritor de bloco do alvo ou metadado ainda desconhecido aborta. O caminho
é limitado a `/proc/PID/fd/N`, com timeout e limite de32 fallbacks por scan.

As duas primeiras rodadas abortaram sem `unlock-intent`: uma por essa
permissão FUSE e outra por divergência de aliases durante a preparação do
loop. A terceira aguardou `udevadm settle --timeout=10` antes do vínculo e
passou. A segunda falha não registrou os valores exatos, portanto sua causa
não foi demonstrada; não atribuir com certeza ao udev. A guarda permanece
estrita e agora informa os valores em eventual divergência. Não houve
trigger, rescan da mídia ou modificação da regra de automount.

O helper público `phase4-p2-qualify.py qualify` não tem entrada para gravar
o cartão. Nele, os únicos SETRO0/escritas recebem os aliases do loop recém
alocado, vinculados por LOOP_GET_STATUS64 ao inode/FS do arquivo temporário.
O cartão passa apenas pelas funções C86 de leitura e SETRO1. Antes/depois,
hash integral da p2 coincide com C86; MBR/prefixo16MiB, CID, geometria,
desmontagem e regra C83 são verificados. O survey da retomada havia encontrado
os quatro aliases RO0; a execução restabeleceu e confirmou RO1 em todos.

Foram aprovados16 casos do primitivo,46 do controlador e24 de transporte/
bootstrap. Estes são testes virtuais; quatro casos adicionais foram medidos
no loop real: gravação integral512MiB/fsck, intents duráveis, transição
RO com p1/p3 protegidas e short-pwrite real de512bytes sem retry/complete,
terminando com quatro aliases RO. A fixture usa fonte sintética ext4 sem
ROM/seed/chaves. O loop foi desconectado e seus dois arquivos grandes
removidos após sucesso. As parciais anteriores e os journals foram preservados.

Privados em `build/phase4/p2-writer`: `copy-qualify.eu471jrh`,
`package-qualify.12vlbtbq`, `controller-checks.xyyryq05`,
`transport-checks.x_ykdtnz`; pointers `latest-complete-qualify`,
`latest-package-qualify`, `latest-controller-checks`, `latest-transport-checks`.
Resultado Deck `/var/tmp/muos-r35s-c87-qualify.0naiv5wo`, recebido e conferido
com journal completo/falha, hashes e fsync no host. Prova pública
`dist/phase4/p2-controller` inclui apenas código/testes/resumo redigido.

Faltam o provisionamento inicial C79, a entrada física de aplicação/recuperação
que derive elegibilidade de backup/imagens/captura, o vínculo com o fence e
o ciclo físico pósboot/recuperação. O controlador genérico sozinho não
autoriza esses passos. Não reutilizar restore C20, rearmar tokens, restaurar
seed antigo após possível boot ou apagar backups C82/C83/C86. O original32
e as referências/SDK/imagens anteriores continuam preservados.
