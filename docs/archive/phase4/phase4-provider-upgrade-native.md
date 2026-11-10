# C72 — provider e muxretro instalados seletivamente

Em 03/11/2026, a transação C71 foi aplicada ao cartão de teste de 128 GB,
no mesmo boot71/UUID C68, em 192.168.15.10. Foram substituídas cinco folhas,
adicionadas26 e removidas12 folhas de metadados/licenças obsoletos do C60.
Criados29 diretórios novos e removidos13 antigos vazios. Os31 arquivos finais
coincidem em hash, modo, owner e link único com o target C67. A raiz retornou
a somente leitura; nenhum serviço, sessão gráfica, reboot ou montagem p3
foi iniciado. Original32 e Steam Deck não foram acessados.

O host instalado agora tem SHA256
`cd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d`.
As quatro bibliotecas de `/opt/muos/frontend/lib` são o provider C65/C68,
modo0644. Os manifestos estão em `/usr/share/muos-frontend-libs` e
`/usr/share/muos-muxretro-provider`; os diretórios antigos do pacote C60
deixaram de existir. Os consumidores gráficos ainda exigem seu contrato
runtime; a variante C46 de seleção de menu continua temporária, sem ser
instalada como biblioteca geral.

O [executor](../../port/scripts/run-phase4-provider-upgrade.py) exigiu a prova
C71, conferiu os17 originais públicos contra o backup local e vinculou boot,
UUID e infraestrutura à evidência C68. Não afrouxou fontes ou guardas dos
incrementos históricos. Plano, backup e implantação foram fsynced no host
antes de permitir RW. O adaptador obtém o lifetime lock, repete guardas de
mídia/quiescência e executa a política exata C71. Seu trap tenta rollback e
sela RO mesmo se a recuperação recusar conteúdo desconhecido.

O [checker do adaptador](../../port/scripts/check-phase4-provider-upgrade-native.py)
passou18casos em container com hardware mockado: aplicação/verify/rollback,
boot/UUID incorreto, token, PCM aberto, host ativo, espaço insuficiente,
readiness/lock, falhas RW/RO/publicação, TERM, drift privado, conteúdo estranho,
source corrompido e argumentos inválidos. O fonte real foi redirecionado em
seis constantes de caminhos para fixtures; os remounts/guardas de hardware
foram simulados. Isso qualifica controle de fluxo, não remount físico sob
falha. Os140casos da transação C71 permaneceram válidos e não foram repetidos.

A aplicação nativa terminou com código0; modelo final, manifestos, fundação97,
101pré-requisitos preservados, fingerprint privado e mounts globais passaram.
Rede/infraestrutura mantiveram os mesmos PID/starttime. A checagem instalada
de dlopen eager das quatro bibliotecas e `muxretro --version/--help` passou.
Não houve execução de core/ROM, som ou GUI neste incremento.

Houve um erro no primeiro comando de checagem: o executor ordenava os nomes
das bibliotecas alfabeticamente. O probe C65 tem ABI posicional: recebe
ui/common/mod/svg e carrega argv3 primeiro, permitindo resolver referências
cruzadas de ui/common no grupo de libmuxmod. Com argumentos ordenados,
carregou svg primeiro e falhou em `lang` antes da CLI do host. Isso não foi
tratado como defeito ou aprovação do payload instalado.

O [resumidor](../../port/scripts/resume-phase4-provider-upgrade.py) preservou
os quatro recibos `native-ABI-positional-failure.*`, conferiu os sucessos de
apply/modelo/mounts e executou somente a branch verify com a ordem C65/C68.
A fonte original, binding e cápsula permaneceram intactos. Não reaplicou a
transação nem executou rollback no console. A prova registra explicitamente
esse ajuste de caller; o executor original permanece como fonte histórica
da implantação, não deve ser usado para uma nova aplicação por rotina.

Stage de recuperação independente:
`build/phase4/provider-upgrade-native/install.otw0lflu`.
Contém backup público17, plano, tar e binding privado, além do stage offline
`provider-upgrade/prepare.agnhn2y8`. Não restaurar contador/seed/keys/saves de
outros backups, nem aplicar rollback C62 de ausência contra o novo pacote.
Rollback dos17 originais só deve ser usado como recuperação explícita,
com guardas adequadas ao estado real; não foi exercido no cartão.

O [fechamento](../../port/scripts/finish-phase4-provider-upgrade.py) confere
novamente o modelo instalado/fingerprint, coleta somente resultados públicos,
remove a cápsula RAM e apresenta “C72 diagnostic finished”. Backup e tar
continuam no computador. A prova `dist/phase4/provider-upgrade-native` exclui
ELF, implantação, UUID, fingerprints privados, ROM e saves. SDK intacto;
imagemC70 não foi gravada. O próximo recorte deve usar um novo vínculo e
guardas para o pacote instalado31, sem executar a guarda antiga C68/C62.
Fluxo gráfico instalado, boot da imagem, autostart permanente, Power/suspend,
SRAM e resistência a perda elétrica continuam separados desta aprovação.
