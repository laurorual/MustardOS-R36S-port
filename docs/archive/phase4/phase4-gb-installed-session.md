# Fase 4 — C59: Game Boy com o store instalado

Concluído em 03/11/2026 no R35S, C07/boot70/IP192.168.15.14. O usuário
restaurou a posição salva por Fn+L2, saiu por Fn+Start e confirmou “Tudo certo”
à pergunta específica de restauração e retorno. A sessão usou o CLI instalado
C57, sem transportar outra cópia do store. Nenhuma nova geração foi gravada.

## Vínculo de boot e implementação

A retomada encontrou boot70, enquanto C54 e C58 foram aprovados no69. O método
de shutdown não foi acompanhado e nenhum reboot foi solicitado pelo agente.
C53 continua limitado ao mesmo boot68; C54 continua exigindo68→69. Essas
fontes, guardas e provas permanecem intactas.

O novo módulo `phase4_gb_installed_session.bind_installed_source` exige recibos
C54 e C58 explícitos, coincidentes com suas provas imutáveis sanitizadas,
mesma identidade/assets e origem69 em ambos. C58 precisa ter passado leitura
RO, limpeza/RAMremovida, rootRO, mounts preservados, CLI instalado sem cópia
ELF e sem writes. O boot atual deve ser exatamente o seguinte, inteiro70;
mesmo contador, saltos e booleanos são recusados. A referência ao hash do
recibo C54 deve coincidir. O vínculo original C53→C54 é validado separadamente
com69, sem fingir que o boot atual é69. Antes e depois da sessão, os hashes e
metadados dos quatro arquivos C57 também são conferidos no aparelho real.
O boot UUID atual difere do C54; isso confirma outro boot observado, sem
qualificar shutdown normal, coldboot controlado ou perda elétrica.

`prepare-phase4-gb-installed-session.py` gera o runner a partir dos bytes
congelados C54, aplicando substituições exatas e recusando deriva da origem.
O checker confirma que essa geração reproduz o arquivo de trabalho. O delta
acrescenta os vínculos C58/C57, substitui o backend/gate pelo C58 e retira
`capsule/save-store`. O dispatcher recebe seu próprio recibo de hash. Core,
ROM, hostC50, bibliotecaUI, runner, worker, sessão, seletor e app-launch C53
são byte-idênticos aos aprovados. O source privado de ROM continua ignorado
pelo Git; não foi alterado ou incluído na prova.

O dispatcher/gate e o backend RO gerado são os mesmos C58, sem ampliar suas
operações. Só status/export são aceitos; prepare/commit e montagem RW não
existem nesse backend. Runtime e estados ficam em RAM; p3 fica ro,noload,
nosuid,nodev,noexec na namespace privada. O teste não instala scripts novos
na raiz e não transforma o diagnóstico em frontend permanente.

Todo código novo é MIT em `port/`. Foram consultados o runner/analisador C54,
a sessão/seletor C53 e o adaptador de leitura C58; não foram modificadas refs
ou recompilados ELFs. A origem de cada payload permanece vinculada aos
recibos anteriores e às licenças já registradas. SDK/Buildroot compartilhado
não foram alterados.

## Verificações

`checks.zebm2adj` passou29casos: vínculo69→70 válido e recusas a mesmo/salto/
booleano, origens divergentes, recibos de falha/limpeza incompleta/RAM retida,
role/outcome/identidade incorretos, rootRW, deriva do store/mounts, p3RW,
ELF alternativo/CLI não instalado, writes no cartão/pacote, geração/tamanho
ou recibo inválidos e divergências de ROM/core/CLI/experimento. Confere também
o delta reproduzível do runner e ausência do ELF do store no payload.

As34fixtures C58 e os testes de falha/lifecycle C45 são reutilizados para os
mesmos bytes, sem repetir API, USB, calibração sonora ou bootstrap comercial.
O novo boot tornou necessária a conferência real do pacote e da leitura na
sessão, sem repetir o ensaio C58 sem GUI.

## Resultado nativo e físico

Stage `build/phase4/gb-installed-session/load.uzlnx4ac`:

- inspectores, fonte/recibos e guardas reais passaram antes da sessão;
- usuário selecionou R35S-Diagnostic com A, entrou com Start, moveu Mario,
  restaurou a posição por Fn+L2 e saiu Fn+Start; retorno confirmado;
-623frames, hotkey, expired0, operação0/cleanup0 e retorno normal ao launcher;
- duas chamadas status e uma export pelo CLI instalado, cada uma com pacote
  conferido; nenhuma cópia ELF do store, inicializador ou save novo enviado;
- PKSTv1/CRC do core/manifesto/assinaturaPNG válidos,26861bytes, metadados antes
  e depois da interação coincidentes;
- HEAD1/0/2 e inventário completo byte-idênticos ao final C58/C54 e entre as
  duas leituras; geração comercial original continua somente no cartão128;
- rootRO0755/fundação97/taint0/PCMclosed, prefs55/70 e hashes de mixer, DRM,
  volume e WirePlumber preservados; infraPIDs/starttime e mounts globais iguais;
- cápsula, ROM/core/host/inspetor/helpers/estados RAM removidos, p3 desmontada
  e tela final “C59 diagnostic finished / No game or menu is running” enviada.

O CSV registrou4callbacks de underrun e1539frames ausentes, sem timestamps que
permitam atribuir causa ao load. A taxa recente do core foi59,9401Hz; não é
throughput absoluto e não se deve dividir623por45, pois a saída foi voluntária.
Não foi feita nova qualificação de continuidade acústica. Power/suspend,
SRAM/GC, longa duração e desempenho NES continuam questões separadas.

C57 permanece instalado/passivo, agora conferido e executado no boot70 após
o69 observado. C12/C25 continuamoff, IRQ/RW/ganho215/quantum1024 e preferências
não foram recalibrados. Original32 e Steam Deck não foram acessados. A imagem
C56 continua privada e não foi gravada ou iniciada no console.

## Reprodução e prova

Com os mesmos recibos, assets e boot previsto, sem repetir a sessão aprovada
por rotina:

```sh
python3 port/scripts/prepare-phase4-gb-installed-session.py
python3 port/scripts/check-phase4-gb-installed-session.py
python3 port/scripts/run-phase4-gb-installed-session.py --host 192.168.15.14 \
  --mode load --boot 70 \
  --source-save build/phase4/gb-persist/save.hi07rjg_ \
  --source-load build/phase4/gb-persist/load.i2to6dts \
  --source-prior build/phase4/gb-reboot/load.x7a7858i \
  --source-installed build/phase4/gb-installed/native.ewspqvb0
python3 port/scripts/analyze-phase4-gb-installed-session.py \
  build/phase4/gb-installed-session/load.uzlnx4ac
python3 port/scripts/package-phase4-gb-installed-session.py
```

A confirmação física está vinculada ao hash da análise da sessão. A prova
`dist/phase4/gameboy-installed-store/SHA256SUMS` contém fontes e metadados
sanitizados, sem ROM, ELF, estado, PNG, INI, PCM, identidade/hashROM/bootUUID
privados ou hashes dos bundles comerciais. Provas anteriores e SDK conferidos
intactos. O pacote de recuperação C57 permanece no host.

Próximo C60 proposto: preparar uma receita Buildroot opt-in para o host nativo
muxretro já validado, verificando origem, licenças, ABI e dependências antes
de qualquer instalação. Manter core/ROM/saves fora do payload e autostart
OFF. Esse passo aproxima a imagem standalone do runtime já aprovado, sem
ampliar escritores duráveis ou repetir a restauração C59. Nenhum C60 armado.
