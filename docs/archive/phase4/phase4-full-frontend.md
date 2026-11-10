# Fase 4 — frontend ampliado e controles reais

Ensaios de 25/10/2026 no R35S `R36S-V12 2023-08-18 Panel 0`.
**Resultado:** frontend nativo, transições entre submenus, áudio de navegação,
volume e brilho passaram em sessões limitadas, usando o userspace próprio
em RAM sobre o kernel instalado. Não houve boot do kernel/rootfs candidato.

## Binários e recursos utilizados

Base: [foundation privada](phase4-private-foundation.md), imagem ext4 SHA256
`43a692d1ef877d60b423a757bbad8305d247022bb67ed632bfa8d890be32ae16`,
281 ELF AArch64, glibc2.41/GCC13.4/SDL2.30.12 e r13p0 integrado.
A [preparação](../../port/scripts/prepare-phase4-frontend-session.sh) extrai
essa imagem por debugfs, confere seu hash e acrescenta recursos e ferramentas
do ensaio. Nenhum binário Debian foi importado.

O frontend é a revisão `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`, com os
patches de board 0003 e, na repetição final, 0006. A compilação usa o mesmo
SDK da base. O staging final recebe os binários recompilados; **o patch0006
e os recursos adicionais ainda precisam ser incorporados à próxima imagem
Buildroot**. Não atribuir essa correção à imagem base anterior por seu hash.

Recursos internos fixados na revisão
`550cc58f9cd3449a17f53ca55efcdc6c473b5a89` (GPLv3):

| Caminho no internal | Git blob |
|---|---|
| `share/info/manifest/core.json` | `016d9bdc27ff0389d3784e735385303aab0116e5` |
| `script/system/assign.sh` | `be73840f57bf54ff2f389377294dcdcdeac191d2` |
| `script/device/audio.sh` | `1b1da45464ee74932f7712577888ea39fa08c70c` |
| `script/device/bright.sh` | `b0ac560cef5ef69460a5eaf15dfb7dd52f3c00af` |
| `script/var/display.sh` | `8046b335fa3f168d5bb352d8d2fae95013e54214` |
| `script/var/governor.sh` | `6c644a9e7af93c729d9583e97a750c56d5b2c624` |

O manifesto, ausente no snapshot mínimo, foi obtido da
[revisão oficial](https://github.com/MustardOS/internal/blob/550cc58f9cd3449a17f53ca55efcdc6c473b5a89/share/info/manifest/core.json),
e seu Git blob conferiu. Os scripts foram lidos dos arquivos locais, também
com conferência por blob. `assign.sh -p` executou nativamente e gerou
**521 associações** no storage privado. A pasta `ROMS` ficou vazia: isso não
aprova instalação, disponibilidade ou execução de cores/emuladores.

## Mapping nativo e inicialização do processo

O novo [muos-sdl-map](../../port/utils/muos-sdl-map.c), AArch64/MIT, consulta
SDL e joydev. Exige exatamente um controle `756d:3504`, nome `muOS-Keys`,
15 botões/4 eixos/1 hat em SDL e 13 botões/6 eixos em joydev, com os códigos
esperados. Volume entra nos índices13/14 adicionados por essa versão SDL.
O utilitário recusa outra versão de SDL até revisão desse contrato.

O mapping observado novamente foi GUID
`06004ca66d750000043500006f730000`, com A:b1/B:b0, X:b2/Y:b3,
Fn:b10, L3:b11 e R3:b12. Foi gravado e relido com `muvarctl`.

Uma falha inicial era da nova ferramenta: ela exigia retorno zero de
`JSIOCGAXMAP/JSIOCGBTNMAP`. O BSP retorna a quantidade de bytes copiados,
como se vê em `build/phase4/linux-base/drivers/input/joydev.c:561–570`:

```c
return copy_to_user(argp, joydev->abspam, len) ? -EFAULT : len;
```

A correção aceita sucesso não negativo e mantém a conferência do descritor.
Não foi uma mudança de mapping físico nem recorrência da ressalva de L3.

Outro ensaio terminou antes da janela visual: `muxfrontend.c:782` instala
`PR_SET_PDEATHSIG` e envia SIGTERM a si próprio quando `getppid()==1`.
O worker Python é PID1 no namespace. O
[executor](../../port/scripts/phase4-frontend-native.py) passou a manter um
shell intermediário que espera pelo frontend, reproduzindo o contrato de pai
vivo esperado pelo programa. O frontend permanece sem wrappers de dispatch
ou execução e recebe SIGTERM diretamente para sair.

Na preparação também foram corrigidos scripts ausentes e os nomes de chaves
de idle: `settings/power/idle_display` e `idle_sleep`, definidos em
`common/config/config.c:246–247`. Não confundir os nomes do schema com os
campos C `idle.display/idle.sleep`. Os resultados negativos foram preservados;
não contam como aprovações de runtime.

## Interface e gráficos

Na sessão silenciosa, o usuário confirmou texto, orientação, A/B/Fn, entrada
e retorno dos submenus. O acompanhamento por `/proc/PID/comm` registrou
`muxlaunch`, `muxinfo`, `muxconfig`, `muxassign`, `muxplore`, `muxcollect`,
`muxhistory` e `muxapp`, dentro do mesmo processo de frontend. O percurso
incluiu ações adicionais do usuário; não houve lançamento de conteúdo.

Antes da interface, EGL/readback passou na imagem extraída, com ARM/Mali-G31,
GLES3.2 r13p0 e leitura `(32,128,191,255)`, sem erro GL. A UI abriu KMSDRM
com o controle correto. A janela silenciosa terminou normalmente após
75,441s. Isso cobre o frontend ampliado nesse recorte, não todos os seus
menus, modos de vídeo ou caminhos de execução.

## Volume e brilho: causa e correção dos dois passos

**Fato de fonte:** `common/ui/common.c:1532–1546` apenas mostra as barras nos
handlers de volume/brilho. Quem executa os ajustes globais é `muhotkey`.
Por isso a UI isolada anterior não demonstrava os helpers reais.

O primeiro ensaio com o daemon revelou duplicidade, também percebida pelo
usuário: o board apontava volume físico em `event3`, enquanto `muinput`
também encaminhava KEY_VOLUME* ao controle virtual. O daemon recebia ambos.
Os logs registraram PRESS/RELEASE e comandos duplicados, com passos de10
em vez de5. O limite de60s terminou durante o teste de brilho; essa sessão
não aprovou a sequência completa.

O [patch0006](../../port/patches/0006-frontend-r35s-normalized-volume.patch)
muda somente o índice de volume bruto no board R35S:

```c
/* muinput forwards volume to the virtual pad; do not also read raw keys. */
{"R35S R36S-V12 Panel 0", "rk-r35s-p0", board_special_none,
 nop, ev0, nop, NO_EVENT_OFFSET, regular},
```

O índice PMIC não foi alterado; Power não foi exposto/testado. A fonte física
de volume continua disponível ao `muinput`; `muhotkey` usa os eventos
normalizados. Outros boards permanecem com seus índices anteriores.

A repetição final teve janela máxima de110s e encerramento solicitado por
SSH aos **87,390s**. O usuário confirmou “tudo está funcionando como esperado”.
Os logs finais têm 7 PRESS/7 comandos de volume− e 3 PRESS/3 comandos de
volume+, em passos de5. Houve mais toques do que o roteiro mínimo; não
inferir quantidades físicas pelo roteiro. Brilho também mudou de5 em5,
entre35 e85 durante as ações, com configuração e sysfs acompanhando.
Ao final, o supervisor restaurou o snapshot inicial80.

Os helpers nativos, antes das ações manuais, passaram nos controles diretos:
volume100→95→100 e brilho80→75→80. Nenhum evento de botão foi injetado.
O [recorte de hotkeys](../../port/device/rk-r35s-p0/session-hotkeys.json)
inclui somente quatro ações, sem hold, idle, Power, suspend ou instalação.
Não considerar essa configuração reduzida o perfil final de energia.

## Áudio e restauração

Navegação e confirmação foram audíveis no frontend completo. O primeiro
ensaio sonoro usou os WAVs originais e o usuário voltou a relatar a ajuda
inaudível/baixa. Na repetição, somente no rootfs temporário,
`info_open.wav/info_close.wav` receberam `confirm.wav` como controle;
originais e substitutos estão identificados por SHA256. A aprovação de
ajuda é limitada a essa substituição. Escolher/adaptar o som final continua
pendente, sem atribuir o problema ao backend de áudio inteiro.

O ensaio usa SDL/PipeWire, software inicialmente em unity para diagnóstico,
com os helpers `audio.sh` ajustando o volume. Isso não muda o preset de boot35.
Na primeira sessão sonora, foi amostrado PCM S32_LE/stereo/44100Hz,
period512/buffer2048, Playback153,153. O mixer foi comparado por snapshot
após cada restauração; não foi elevado ao máximo do codec237.

Apenas o arquivo de valor do backlight recebeu bind com escrita no namespace.
O restante de sysfs e proc ficou somente leitura; `/dev/fb0`, blocos e PMIC
não foram expostos. O `bright.sh R` inicial tenta escrever `fb0/blank` e recebe
EROFS nesse ambiente. A UI permanece visível via KMS; **blank/retorno de blank
não foram aprovados**. Não reintroduzir mmap de framebuffer por causa deste teste.

O [supervisor](../../port/scripts/phase4-core-session.py) salva o brilho e o
restaura/confronta após os serviços, além da restauração já verificada do mixer.
Para os novos modos frontend, o worker tem limite160s e o restaurador
independente200s. O disparo forçado desse segundo timer continua sem ensaio.
Todas as sessões foram coletadas e removidas de `/tmp`; kernel instalado
inalterado, taint0, cinco contadores Btrfs0, serviços do dArkOSen ativos,
mixer igual ao snapshot e brilho80. Nenhuma imagem foi gravada/reparticionada.

## Checkpoint e próximos contratos

Staging final privado SHA256
`eba4fd85f473be6c28b8c2967e0b21477777c9974751c3a57fe0ad784b91b365`;
`muxfrontend` SHA256
`bb4ea22d12b2e9a6da52aef1b4c0abd162eeb038e5f78bca5cbbfffa3e0e7d66`;
mapper SHA256
`7ee35bca4528477e3e0d692765a6e813e0fc00bc3c539632fa03e91d71dfe4f2`.
O staging não é firmware gravável. Imagens e Mali permanecem privados.

Provas e fontes estão no
[checkpoint](../../dist/phase4/frontend-full-native/native-results.json)
`dist/phase4/frontend-full-native/`, com hashes de todos os arquivos.
Inclui as dez sessões (inclusive preflights negativos e a duplicidade),
aprovações do usuário, fontes/patches/scripts e binários próprios. Exclui
imagem, tar do rootfs, ZIP e ELF Mali. O agrupamento de resultados identifica
separadamente a sessão final aprovada; status0 de uma tentativa anterior não
substitui a confirmação funcional.

Antes de um cartão independente: incorporar patch/recursos/mapper à receita,
reconstruir a imagem e auditar seu conteúdo; completar ordem do init e
shutdown, autostart/espera do controle e geração de mapping, módulos e firmware
do BSP e cadeia de boot. Incluir bateria, power, blank, suspend, persistência
após reboot e ensaios prolongados nas próximas validações. O som original de
ajuda ainda requer decisão de produto. O kernel candidato continua sem boot.
