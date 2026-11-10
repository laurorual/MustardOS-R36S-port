# C19 — preparação de preferências com raiz somente leitura

Preparação em29/10/2026 com o saldo limitado solicitado pelo usuário. Escopo:
um componente pequeno testável e um plano de integração; sem novo boot/menu,
particionamento, formatação, instalação persistente ou regressão de Wi-Fi.

## Estado real conferido por leitura

Console permanece39/C07, SSH fixado192.168.15.17:2222, rootext4RO/FAT desmontada/
taint0, btusb ausente, rede e55 pré-requisitos íntegros. Política Wi-Fi-only
permanece instalada. Cartão original32 preservado; nenhuma escrita física
nova foi habilitada. Inventário do cartão128 (setores de512bytes):

| Região | Início | Setores | Estado |
| --- | ---: | ---: | --- |
| p1/MUOSDIAG |32768 |204800 | FAT100MiB, desmontada |
| p2/ROOTFS |262144 |1048576 | ext4 de512MiB, raizRO |
| após p2 |1310720 | — | sem p3 apresentada pelo kernel |
| dispositivo inteiro |0 |249872384 |127934660608bytes |

Dadosrw ainda NÃO existem. Não confundir espaço livre no cartão com um
filesystem montável. P3 alinhada após1310720 é possibilidade para /userdata,
não um plano de gravação aprovado/implementado por esta preparação. Antes de
qualquer alteração: coletar tabela real completa, preservar disk-id/bootprefixo/
p1/p2 e seus PARTUUIDs, escolher tamanho/recuperação e comparar plano sem escrita.
Preferir operação offline a tentar reler tabela de partições com raiz viva.
Nunca fsck na raiz montada. Original32 não será usado como destino de trabalho.

## Decisões de integração fundamentadas no upstream

Leitura de refs/muos/internal/script/var/audio.sh:63–105: política3 força máximo;
policy0 cai em GET_SAVED_AUDIO_VOLUME. S80pipewire.sh:374–436/448–483 também
carrega volume por saída via LOAD_SINK_VOLUME. Portanto só bindar settings ou
trocar3→0 não basta se um slot antigo sobrepuser o valor global restaurado.

bright.sh persiste settings/general/brightness em unidades0..160, mas blank0
é transitório e o helper normal salva no mínimo1. O primeiro recorte de bancada
limita armazenamento a40..160, faixa já aceita pela restauração C11. A faixa
completa baixa/blank deverá ser qualificada separadamente; não inventar escala
percentual nova. Volume é software0..100; codec157/rotaSPK_HP/overdrive0 continuam
templates, não preferências graváveis nem nova calibração acústica.

C11 session/runtime.sh copia config/device-config/volume para RAM e reaplica
perfil21 a cada geração. S90 exige /userdata em filesystemrw e cria diretórios.
worker.sh ainda remonta a raiz privadaRW; além do armazenamento, S80 restaura
/etc/asound.conf e /usr/share/alsa/alsa.conf. Não remover esse remount sem
auditar/bindar em RAM todos os destinos que ainda precisam ser gravados.

Abordagem escolhida: manter templates/perfil C10 e estado de execução privados
em RAM; persistir somente um par tipado volume/brilho num registro versionado.
Não bindar a árvore global inteira nem restaurar cache/ready/PIDs após reboot.
Validar perfil aprovado antes de aplicar os três overrides dinâmicos (volume,
brilho e boot-policy0) e registrar esses valores separadamente dos hashes
estáticos. Fonte C10/21 originais e rollback da sessão precisam continuar
comprovados. Nenhum arquivo C10/C11/C12 foi alterado nesta rodada.

## Componente preparado

port/utils/muos-preferences.c, código originalMIT, sem fonte upstream copiada.
CLI exige diretório existente/root0700 e marcadorroot600 conhecido; não cria
nem formata storage, não remonta raiz, não aplica áudio/brilho ou edita init.
Aceita magic ext* e tmpfs, recusa filesystemRO; o futuro adaptador deve exigir
ext4 e identidade real de mount/CID/PARTUUID. A ferramenta genérica não substitui
essa guarda de placa/montagem. Não instalar ou chamá-la como serviço ainda.

Registro canônico único:

```text
MUOS-PREFS-1
VOLUME=60
BRIGHTNESS=75
```

init cria100/80 só quando o arquivo está ausente. Dado existente válido é
preservado; formato desconhecido/corrupto é recusado, sem defaults por cima.
load lê; save exige registro válido anterior. Campos extras/flags, números
não canônicos, links, permissões/owner indevidos e caminhos com symlink são
recusados. Sem sourcing/eval ou nomes de saída arbitrários. Lock não bloqueante
serializa o par; valor igual não causa nova gravação. Staging exclusivo→fsync
arquivo→rename→fsync diretório. Staging desconhecido é preservado/recusado.

Falha antes de rename preserva o registro anterior. Falha de fsync do diretório
APÓS rename retorna74: o novo valor pode estar visível, mas a durabilidade é
incerta; não anunciar sucesso nem tentar rollback automático. Isso não é prova
contra queda elétrica real. A versão de teste com injeção de falhas nunca deve
ser enviada ao console. Contrato em preferences/contract.json mantém enabledfalse.

## Verificações e limites

check-phase4-preferences.py compila produção e fixture em container/SDK
existente, ARMv8-A/Cortex-A35, C11/PIE/RELRO/NOW e warnings como erro. SDKconfig
preservada.16 casos no AArch64/QEMU sobre arquivos tmpfs reais: primeiro uso,
save/load por processos distintos, init sem sobrescrever, ausência de rewrite
de valor igual, faixas/formato, versão desconhecida, symlink/hardlink/ancestral,
staging alheio, marcador/permissões, lock ocupado e falhas antes/depois do rename.

Primeira fixture vkm0szva recusou64 no início por resolução de / sob prefixo
QEMU, antes de qualquer teste de mídia. Corrigido o harness para invocar o
loaderAArch64 explicitamente com prefixo/, mantendo libc do sysroot; fixtures
passaram no stage checks.6hmt3nzp. Não houve modificação da segurança do helper
para contornar essa diferença de emulação.

Teste nativo limitado a /run: audit-phase4-preferences-ram.py transfere só o
binário de produção validado, cria diretório temporário próprio em tmpfs,
init→save60/75→init→load, recusa101 e remove binário/dados ao terminar. Esse
teste NÃO aplica60/75 ao hardware e não comprova ext4/reboot/persistência real.
Resultado aprovado no39/C07: init100/80→save60/75→novo init preservando60/75,
load60/75 e recusa101RC64. Brilho real80 antes/depois, rootRO/FAT desmontada/
taint0 e rede pronta conferidos. Binário e diretório RAM removidos na mesma
execução. Resultado/saídas em checks.6hmt3nzp/native-analysis.json, separados
das fixtures. Nada foi instalado em /usr ou /etc e nenhum reboot foi pedido.

## Próxima rodada, com orçamento restaurado

1. Conferir checkpoint/saúde e política Wi-Fi-only. Não repetir ensaios USB.
2. Qualificar primeiro um mount ext4 de laboratório, por exemplo imagem pequena
   em RAM/loop e namespace privado, com identidade/ownership e cleanup, root
   globalRO. Validar loop/utensílios disponíveis antes; não adotar loop alheio.
3. Testar registro60/75 através de unmount/remount dessa imagem; recusar mídia
   errada/RO/ausente sem formatação e sem tocar o cartão original. Ainda não
   equivale a sobreviver reboot: imagemRAM é deliberadamente volátil.
4. Preparar tabela de dados reais e transação offline com rollback verificável,
   preservando p1/p2/bootprefixo. Criar defaults apenas no primeiro uso.
5. Integrar opt-in ao lifecycle C11 com RAM overrides, política salva0/slot da
   saída coerente, cache reconstruído e identificação dos demais rootwriters.
   Não começar C12 no C07 nem reler seed para fazer esse teste.
6. Só então ensaio nativo de volume60/brilho75→stop/start→valores iguais e,
   depois, reboot controlado. Confirmar hardware/cache/perfil original, rootRO,
   Wi-Fi/SSH/taint0 e recuperação de mídia. Manter lease e menu permanenteoff.

Persistência de preferências segue DESABILITADA. Este recorte prepara a base;
não afirma que salvar preferências ou dadosrw já estejam integrados ao firmware.
