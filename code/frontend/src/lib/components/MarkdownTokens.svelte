<script lang="ts">
  import type { Token, Tokens } from 'marked';
  import Self from './MarkdownTokens.svelte';
  let { tokens }: { tokens: Token[] } = $props();
</script>

<!-- Renders tokens as elements instead of {@html}: model output is untrusted, so raw HTML stays text and links and images never load. -->
{#snippet inline(token: Token)}
  {#if 'tokens' in token && token.tokens}<Self tokens={token.tokens} />{:else}{'text' in token
      ? token.text
      : token.raw}{/if}
{/snippet}

{#each tokens as token, index (index)}
  {#if token.type === 'space' || token.type === 'def' || token.type === 'checkbox'}
    <!-- nothing to show -->
  {:else if token.type === 'heading'}
    <svelte:element
      this={`h${Math.min(token.depth + 2, 5)}`}
      class="mt-4 mb-2 text-[17px] font-extrabold text-ink"
    >
      {@render inline(token)}
    </svelte:element>
  {:else if token.type === 'paragraph'}
    <p class="mb-3">{@render inline(token)}</p>
  {:else if token.type === 'strong'}
    <strong class="font-extrabold text-ink">{@render inline(token)}</strong>
  {:else if token.type === 'em'}
    <em>{@render inline(token)}</em>
  {:else if token.type === 'del'}
    <del>{@render inline(token)}</del>
  {:else if token.type === 'codespan'}
    <code class="rounded-sm bg-surface px-[5px] py-0.5 text-[13px]">{token.text}</code>
  {:else if token.type === 'code'}
    <pre class="mb-3 overflow-x-auto rounded-xl bg-surface p-4 text-[13px]">{token.text}</pre>
  {:else if token.type === 'br'}
    <br />
  {:else if token.type === 'hr'}
    <hr class="my-2 border-line" />
  {:else if token.type === 'blockquote'}
    <blockquote class="mb-3 border-l-3 border-line pl-4">{@render inline(token)}</blockquote>
  {:else if token.type === 'list'}
    {@const list = token as Tokens.List}
    <svelte:element
      this={list.ordered ? 'ol' : 'ul'}
      class={['mb-3 pl-10', list.ordered ? 'list-decimal' : 'list-disc']}
      start={list.ordered ? list.start || 1 : undefined}
    >
      {#each list.items as item, position (position)}
        <li>
          {#if item.task}{item.checked ? '☑ ' : '☐ '}{/if}<Self tokens={item.tokens} />
        </li>
      {/each}
    </svelte:element>
  {:else if token.type === 'table'}
    {@const table = token as Tokens.Table}
    <div class="mb-3 overflow-x-auto">
      <table class="border-collapse">
        <thead>
          <tr>
            {#each table.header as cell, column (column)}<th
                class="border border-line px-3.5 py-1.5 text-left font-bold"
              >
                <Self tokens={cell.tokens} />
              </th>{/each}
          </tr>
        </thead>
        <tbody>
          {#each table.rows as row, line (line)}
            <tr>
              {#each row as cell, column (column)}<td class="border border-line px-3.5 py-1.5">
                  <Self tokens={cell.tokens} />
                </td>{/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    {@render inline(token)}
  {/if}
{/each}
