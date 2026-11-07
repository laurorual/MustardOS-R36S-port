# Fase 4 — C10: perfil reproduzível e integração com Buildroot

O perfil privado reúne os valores aprovados em C06/C09. Não altera a candidata
instalada nem habilita menu no boot. O pacote data-only e um hook explícito
permitem reproduzir esses dados em novas imagens sem manter as substituições
espalhadas pelos executores de diagnóstico. Perfil gerado validado nativamente no recorte temporário descrito ao final.

## Fonte e política

`port/device/rk-r35s-p0/runtime-profile.json` fixa Panel0/board, SPK_HP/157,
volume software100/política3, incremento5, backlight80/max160, overdrive0,
sound2, debug2 e idle0. A política3 é a mesma de bring-up que usa o máximo
de software, sem carregar níveis antigos por saída. Não é política final de
preferências persistentes ou calibração sonora. UIenabled0/hotkeys1 e
coreaudio1/input1 são defaults distintos; nenhum rcS completo é habilitado.

Navegação é regenerada a partir do WAV na revisão interna
550cc58f9cd3449a17f53ca55efcdc6c473b5a89: ganho linear limitado a pico30000,
sem mudar amostragem/duração/chunks RIFF; SHA adac7879…bb3ee igual ao C06/C09.
Ajuda recebe o confirm original, como nos ensaios aprovados. GPLv3 de upstream
foi relida; fonte dos recursos, proveniência e LICENSE acompanham o pacote.
Código próprio e dados de integração têm MIT em port/LICENSE. Sem novos blobs.

## Receita e ordem de aplicação

`port/buildroot/package/muos-r35s-profile/` depende de muos-core e instala um
payload separado em /usr/share/muos-r35s-profile. A opção é selecionada pelo
fragmento phase4-runtime.fragment, explicitamente opt-in. O Makefile do
Buildroot fixado, linhas823–839, copia BR2_ROOTFS_OVERLAY depois dos pacotes,
antes de BR2_ROOTFS_POST_BUILD_SCRIPT. Instalar os defaults só pelo pacote
permitiria que o overlay antigo recolocasse SPK/95/35.

Por isso phase4-runtime-post-build.sh chama apply-phase4-runtime-profile.py
após o overlay. O aplicador valida board, manifesto, hashes, lista exata de
arquivos, modos0644, paths/parents sem symlinks e UIenabled0 antes da primeira
escrita. Usa replace atômico por arquivo, rollback de alterações aplicadas em
falha e recusa targets fora do contrato. Não é script de init do dispositivo.
Não se deve adicionar o fragmento a uma imagem de produção sem a validação
correspondente; integrações futuras com outros hooks devem preservar sua ordem.

prepare-phase4-runtime-profile.py usa somente git show de refs/payloads
públicos fixados; não lê perfil de rede, seed, chave privada ou raiz viva.
Não modifica refs ou o SDK/configuração da compilação anterior.

## Validação no host

check-phase4-runtime-profile.py passou dez casos: regeneração byte idêntica,
macro real de instalação do pacote, aplicação após overlay, idempotência,
board incorreta, corrupção antes de escrever, autostart mesmo com hash
atualizado, path extra, parent symlink e rollback após falha no segundo
replace. A macro foi exercitada por harness make sem compilar dependências
não relacionadas. Não equivale a uma imagem completa Buildroot reconstruída.

Um output Kconfig separado selecionou pacote/hook e analisou os metadados da
receita real. O output/SDK mutável anterior não foi reconfigurado. Ainda não
houve build completo do firmware nem boot com esses defaults instalados.

## Menor ensaio nativo

prepare-phase4-profile-session.py consome o payload instalado pela macro real
e passa os arquivos a uma sessãoRAM derivada do C09 aprovado. As configs,
asound/defaults, atalhos e três WAVs gerados entram no namespace privado;
checksums devem provar todos os arquivos ativos antes de habilitar a UI
apenas nessa sessão. O menu60s não terá bipes de referência. Helpers CLI e
restauração C09 continuam; rede/RNG/udev são compartilhados, sem reboot ou
novo seed. Defaults UI/atalhos ganham snapshot/readback próprio no cleanup.

Usuário confirma menu/submenus/ajuda e áudio, sem volume/brilho/Power nessa
rodada. Depois: restaurar mixer/config/cache/pasta de volume/brilho/DRM,
retirar os binds adicionais e verificar rootro/taint0/SSH, preservando as
ressalvas de escala visual, loudness e reboot Wi-Fi. Só então aprovar o perfil
no recorte da bancada. Init permanente e preferências persistentes ficam para
incremento separado; não promover toda a sequência de diagnóstico a firmware.


## Primeiro ensaio e formato nativo dos valores

A primeira sessão session.0sqz6utd parou antes do menu:19 hashes passaram,
mas brilho/volume foram regravados pelos helpers depois da aplicação. CLI
95→100/75→80 passou e o cleanup restaurou tudo, rootro/taint0/SSH mantidos.
Prova negativa runtime-profile-config-format-failure. O fonte
frontend/common/config/var_store.c:333–334 escreve strlen(value), sem newline;
o payload de build usa newline nos arquivos textuais. Não equivale a valor
incompatível, mas a verificação estava posicionada depois dos consumidores.

Correção: verificar todos21 arquivos ativos antes de iniciar core/helpers;
depois exigir novamente19 hashes estáticos e consultar volume100/brilho80 no
cache/backlight. Registrar também o tamanho dos dois valores canônicos.
Nenhum hash de asset/default estático é dispensado. Profile/helper fonte
geral não foi mudado por isso; apenas o executor de verificação temporário.


## Repetição aprovada

Pacote session.rxvlawrp consumiu o payload instalado pela macro de pacote e
hook reais:21 hashes ativos pré-core passaram;19estáticos pós-setters e
volume100/brilho80 no cache/backlight passaram. Leituras confirmaram3bytes
para100 e2bytes para80, coerentes com gravação semLF. Defaults continuam
UIdisabled0 enquanto o harness habilita somente a instância da sessão.
Menu60s sem bipes, navegação/submenus/ajuda/sons confirmados pelo usuário.
36probesSSH/29comUI/60,86s simultâneos; identidade rede/udev preservada.

Mixer, verificações C09, defaults UI/atalhos, cache/pasta de volume/DRM/brilho
restaurados. Raizro/FAT desmontado/taint0 e saúde selecionada passaram.
Prova runtime-profile-session; RAM removida depois de processo encerrado.
Quatro grupos de prova C10 tiveram SHA reconferido. O .config do SDK mutável
permanece igual ao baseline network-tools (24fe1d62…e09c85).

Esse resultado valida dados gerados/receita/hook e seu consumo temporário
pelos serviços/ABI já testados. Não é validação de imagem inteira nova ou
init definitivo: o cartão permanece C06r4+C07r3, sem pacote/perfil C10
permanente nem autostartUI. O executor ainda usa a bancada C06/C09; próximo
incremento deve consolidar lifecycle/init próprio consumindo esse perfil,
com contrato de configuração persistente e saída controlada. WarmbootWi-Fi,
calibração sonora e percepção da barra de brilho continuam pendentes.
