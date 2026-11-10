# Fase 4 — C55: store de snapshots como pacote Buildroot

Em 02/11/2026, o utilitário genérico C52 foi integrado como pacote opcional
`BR2_PACKAGE_MUOS_SAVE_STORE`. O padrão continua desativado, inclusive no
perfil existente. Habilitá-lo seleciona zlib, sem selecionar serviços muOS.
A integração acrescenta o CLI, seu contrato, a licença MIT e o manifesto.
Não instala ROM, core, identidade de conteúdo, save, adaptador de mídia,
configuração de sessão, serviço ou inicializador de dados.

## Implementação e referências

O código original permanece em `port/utils/muos-save-store.c`, byte-idêntico
ao C52. A receita em `port/buildroot/package/muos-save-store/` restringe a
seleção a AArch64, declara `zlib` e a licença MIT com hash de `port/LICENSE`.
Compila PIE com stack protector, RELRO/NOW e avisos tratados como erros.
O pacote instala exatamente:

- `/usr/libexec/muos-save-store/muos-save-store`, modo 0755;
- `/usr/libexec/muos-save-store/payload.sha256`, modo 0644;
- `/usr/share/muos-save-store/contract.json`, modo 0644;
- `/usr/share/licenses/muos-save-store/LICENSE`, modo 0644.

O manifesto cobre os outros três arquivos com caminhos absolutos. Ele é
separado da fundação nativa de 97 arquivos: a presença do utilitário não
habilita seu uso por serviços existentes.

Foram consultados o Kconfig e `package/pkg-generic.mk` do Buildroot usado pela
bancada, além das receitas locais de sessão/perfil. No método `local`, a
coleta `legal-info` arquiva a árvore de fontes inteira, independentemente das
exclusões do rsync de compilação. Por isso o preparador copia exclusivamente
`muos-save-store.c`, `LICENSE` e `contract.json` para
`build/phase4/save-store-package/source/`, montado como
`/work/save-store-package/source` no container. A receita usa esse caminho,
seguindo a convenção dos outros pacotes da bancada. Fontes existentes que
não coincidam são recusadas; não há atualização silenciosa da árvore.

O CLI conserva o contrato C52: diretório próprio 0700 e marker exclusivo,
identidade explícita, gerações imutáveis, HEAD atômico, fsync/flock, recuperação
anterior explícita e limite de 32 gerações, sem GC. O chamador ainda precisa
validar mídia, namespace e montagem, criar marcadores com exclusividade e
fsync, parar o writer e inspecionar o estado antes de publicar. Não se deve
invocá-lo diretamente no store comercial por estar instalado num rootfs.

## Verificações realizadas

`build-phase4-save-store-package.py` usa container sem rede, SDK existente e
um `O=` isolado. Executa Kconfig, rsync e `legal-info` reais do Buildroot:

- pacote e zlib ausentes na configuração mínima padrão;
- opt-in seleciona pacote/zlib/libzlib, sem core/session/boot/launcher;
- seleção recusada ao trocar AArch64 por i386;
- rsync contém somente as três fontes autorizadas;
- arquivo de fontes produzido por `legal-info` contém exatamente essas fontes,
  byte a byte, e a licença recolhida coincide com MIT/hash declarado;
- macros reais de compilação/instalação geram somente os quatro arquivos
  previstos, com permissões e manifesto válidos;
- ELF AArch64 PIE, ABI Linux 4.4.0, intérprete
  `/lib/ld-linux-aarch64.so.1`, dependência `libz.so.1`, sem RPATH/RUNPATH;
- loader A35/QEMU com `LD_BIND_NOW=1` resolve as dependências no rootfs C38;
  o CLI sem argumentos recusa com status 64.

O ELF resultante tem SHA256
`e9540c40e00a9b46b3eee0efbb2a669bdc16f6721359a1fd2a1800836929056d`,
**byte-idêntico ao C52**. As 34 fixtures e o laboratório ext4 nativo C52 são
reutilizados para esses mesmos bytes, sem repetir testes já aprovados.
Não foi feito rebuild completo do toolchain/rootfs pelo Buildroot.

Recibos locais: compilação `build.yky74oaa`, composição
`composition.d0qpit_q` e conferência somente leitura `health.qi5uzt8u`,
em `build/phase4/save-store-package/`. A tentativa anterior do ensaio de
arquitetura não trocava a seleção porque `utils/config` normaliza maiúsculas;
a chamada final usa `--keep-case` e confirma i386 no arquivo resultante.
As tentativas intermediárias são preservadas, mas não compõem a prova final.

`compose-phase4-save-store-package.py` copia a árvore privada C38, valida seu
inventário e imagem de origem, e executa a macro real de instalação do novo
pacote. O resultado adiciona somente quatro arquivos e três diretórios,
preserva todos os itens anteriores e passa novamente o contrato C07:
fundação97, payload15, perfil21, contador de fábrica0, defaults desativados,
sem estado privado ou tokens. O loader A35/QEMU também passa nessa composição.
A imagem C38 de 512 MiB permanece inalterada; neste incremento foi composta
uma **árvore privada**, sem gerar outra imagem ou testar boot dela.

O guard de linhagem do compositor C23/C38 foi atualizado para aceitar a
extensão exata do menu C55. Ele continua instalando apenas seus pacotes
explicitamente nomeados; a integração opcional do store usa o adaptador C55.
Não foi reexecutada a composição completa antiga nem alterada sua prova
congelada.

A tentativa de lint adicional `utils/check-package` ficou indisponível porque
o container não contém o módulo Python `magic`. Nenhuma dependência foi
instalada no host. As verificações funcionais acima foram executadas; esse
lint não é declarado aprovado.

## Reprodução e limites

Na raiz do repositório, com os mesmos inputs C38/C52 e SDK preparados:

```sh
python3 port/scripts/build-phase4-save-store-package.py
python3 port/scripts/compose-phase4-save-store-package.py
python3 port/scripts/package-phase4-save-store-package.py
```

A última etapa congela uma prova nova e recusa sobrescrever um artefato
existente. Relatórios e fontes ficam em `dist/phase4/save-store-package`, com
SHA256SUMS; ELF, arquivo de fontes compactado, rootfs e dados privados ficam
fora dessa prova. As provas C52/C54 e o `.config` compartilhado do SDK foram
conferidos sem alterações.

O console permaneceu C07/boot69, sem executar o pacote novo, iniciar menu,
armar C12/C25, montar p3 ou pedir reboot. O cartão original de 32 GB e o Steam
Deck continuam fora do fluxo. Não houve instalação no cartão de teste.
Persistência comercial C53/C54, IRQ/RW/ganho215/quantum1024 e preferências55/70
não foram alterados.

Próximo C56: produzir uma imagem ext4 **privada e offline** a partir da árvore
C55 e validar inventário de readback, fsck e contrato de boot/manifests.
Manter writer/autostart desativados e não instalar/rearmar/flashar para essa
verificação. Uma futura implantação precisa de plano seletivo e rollback
antes de alterar a raiz do cartão. Power/suspend, perda elétrica, GC, SRAM,
continuidade de áudio e performance NES permanecem questões separadas.
