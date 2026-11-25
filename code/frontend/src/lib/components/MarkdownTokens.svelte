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
    <svelte:element this={`h${Math.min(token.depth + 2, 5)}`}>
      {@render inline(token)}
    </svelte:element>
  {:else if token.type === 'paragraph'}
    <p>{@render inline(token)}</p>
  {:else if token.type === 'strong'}
    <strong>{@render inline(token)}</strong>
  {:else if token.type === 'em'}
    <em>{@render inline(token)}</em>
  {:else if token.type === 'del'}
    <del>{@render inline(token)}</del>
  {:else if token.type === 'codespan'}
    <code>{token.text}</code>
  {:else if token.type === 'code'}
    <pre>{token.text}</pre>
  {:else if token.type === 'br'}
    <br />
  {:else if token.type === 'hr'}
    <hr />
  {:else if token.type === 'blockquote'}
    <blockquote>{@render inline(token)}</blockquote>
  {:else if token.type === 'list'}
    {@const list = token as Tokens.List}
    <svelte:element
      this={list.ordered ? 'ol' : 'ul'}
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
    <div class="table">
      <table>
        <thead>
          <tr>
            {#each table.header as cell, column (column)}<th>
                <Self tokens={cell.tokens} />
              </th>{/each}
          </tr>
        </thead>
        <tbody>
          {#each table.rows as row, line (line)}
            <tr>
              {#each row as cell, column (column)}<td><Self tokens={cell.tokens} /></td>{/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    {@render inline(token)}
  {/if}
{/each}
