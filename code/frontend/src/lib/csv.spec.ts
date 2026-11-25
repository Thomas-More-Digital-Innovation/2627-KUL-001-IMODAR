import { describe, expect, it } from 'vitest';
import { toCsv } from './csv';

describe('toCsv', () => {
  it('quotes separators, quotes and line breaks', () => {
    expect(toCsv(['a', 'b'], [['x,y', 'say "hi"\n']])).toBe('a,b\r\n"x,y","say ""hi""\n"');
  });

  it('keeps negative numbers but neutralises formulas', () => {
    expect(toCsv(['v'], [[-1], ['=1+1'], [null]])).toBe("v\r\n-1\r\n'=1+1\r\n");
  });
});
