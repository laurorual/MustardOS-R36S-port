# C21 — edição pelos botões e retenção após reboot

Em 29/10/2026, o usuário alterou as preferências no launcher: um toque em
volume−, depois Fn + volume−. O executor mediu 60/75 → 55/75 → 55/70, sem
injetar eventos. O par novo foi salvo ao encerrar a sessão, recarregado numa
segunda sessão e aplicado novamente após o reboot normal C07 42→43.

O software de volume retornou 0.55 e o backlight físico retornou 70. Isso
qualifica este par na sessão opt-in do Panel 0; não habilita boot permanente,
Power, suspend, fones, calibração de áudio ou outros painéis.

## Implementação do ensaio

O executor `port/scripts/audit-phase4-preferences-session.py` ganhou operações:

- `physical-edit`: parte de um par conhecido, espera uma redução de cinco em
  cada valor por botões reais e exige duas medições consecutivas do alvo antes
  de parar a sessão. Lease de 300 segundos; janela física de 180 segundos.
  Uma segunda sessão deve carregar e aplicar o novo par.
- `verify-after-reboot`: exige `--after-boot`, verifica um contador de boot
  posterior e executa uma única sessão com o par esperado. Não inicializa nem
  reseta o store e não modifica os componentes instalados.
- `stable`: preserva a verificação anterior, agora com par explícito opcional.

O pacote de runtime usado continua sendo service.jbuopxfi, com os mesmos
ELF/scripts/perfil já aprovados em C21. Nenhuma recompilação ou substituição
no cartão foi necessária. As cópias em /run foram conferidas e removidas após
cada ensaio. A receita e o código do aparelho não mudaram neste incremento.

O novo `reboot-phase4-preferences-session.py` exige primeiro provas físicas
congeladas, duas sessões aprovadas e confirmação de novo inode no registro.
Depois exige C07, raizRO0755, p3 desmontada, seed parado, ausência de C12.once,
Bluetooth ausente, quiescência e os 55 hashes. Pede reboot normal ao PID1 em
chamada separada. Não usa reboot forçado nem recarrega seed no kernel vivo.

O empacotador aceita destinos separados para preservar as provas C21 anteriores.
Os relatórios são coletados por lista explícita; não incluem /root, credenciais,
seed, árvore de dados ou logs gerais do aparelho.

## Resultado físico no boot 42

Stage: build/phase4/preferences/session-native.ofzrkwow.
Gerações: run-0004 e run-0005.

A primeira carregou 60/75, chegou ao launcher e mediu a alteração feita pelo
usuário. Após parar UI/hotkeys e antes do ramp de S80, o checkpoint salvou
55/70. O registro mudou inode 1798150→1798176: houve substituição atômica real,
em vez do save sem rewrite exercitado na primeira qualificação C21.

A segunda sessão, após desmontar e montar p3 novamente, carregou 55/70,
confirmou volume real 0.55 e brilho físico 70 e parou com resultado zero.
Os hashes originais, mixer, DRM, slots e configurações foram restaurados.
Brilho de diagnóstico restaurado para 80; raiz privada e global RO, root0755,
p3 desmontada, mountinfo global idêntico, taint0 e rede preservados.

Provas: dist/phase4/preferences-session-physical-edit, incluindo sequência
medida, confirmação do usuário, inodes, fonte testada e logs públicos limitados.

## Reboot e recarga no boot 43

Reboot: build/phase4/preferences/session-reboot.ogukgluu.
O SSH com chave fixada voltou no mesmo IP 192.168.15.19:2222; a verificação de
retorno passou na terceira tentativa. C07/raizRO/Wi-Fi/55 hashes passaram.
Nenhuma reconexão física do dongle foi solicitada nesta transição.

Reload: build/phase4/preferences/session-native.ncyvnvb6, geração run-0001 no
novo boot. O store existente carregou 55/70 e a sessão aplicou esses valores
ao hardware, com first paint e supervisor vivos. Stop/checkpoint e restauração
passaram novamente; pacote RAM removido. Estado final: C07, rootRO0755,
p3/FAT desmontadas, brilho80, taint0, rede, 55 hashes e zero assinaturas
selecionadas de erro de kernel/storage.

Provas de reload em dist/phase4/preferences-session-reboot. O pedido e retorno
do reboot estão em dist/phase4/preferences-session-reboot-transition, com hashes
dos relatórios físico e de reload para ligar as duas etapas. Todos têm SHA256SUMS;
as provas anteriores foram preservadas.

## Estado para o próximo incremento

O par atual no cartão é **55/70**. Não executar novamente os diagnósticos C20
hardcoded60/75 como se esse ainda fosse o valor esperado. A qualificação C20
41→42 permanece válida como histórico; não autoriza resetar preferências.

A integração permanente continua desabilitada; C12 está inativo, sem token,
allow_power0. O cartão original dArkOSen32 não foi usado. O Steam Deck continua
fora do fluxo e já limpo; backup privado640MiB íntegro permanece apenas no host.

A preparação seguinte foi concluída em [C22](phase4-session-package.md):
a guarda de dados passou a usar a função carregada pelo próprio pacote,
manifesto de payload passou a ser obrigatório no opt-in e as dependências
util-linux foram declaradas. Uma sessão com muos-boot oculto passou no43.
Isso não repetiu a edição física nem o reboot aqui descritos. O próximo passo
é compor/conferir o rootfs candidato antes de um novo ensaio de boot.
