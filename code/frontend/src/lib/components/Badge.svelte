<script lang="ts">
  let { status }: { status: string } = $props();
</script>

<span class={status.toLowerCase()}>{status}</span>

<style>
  span {
    display: inline-block;
    padding: 5px 20px;
    border-radius: 14px;
    background: #e6f3ec;
    color: #2e6d50;
    font-size: 12px;
    font-weight: 600;
  }
  .invited,
  .draft {
    background: #fff3d9;
    color: #805e15;
  }
  .suspended {
    background: #fbecec;
    color: #9c4545;
  }
  .archived {
    background: #e9eef1;
    color: #576f77;
  }
</style>
