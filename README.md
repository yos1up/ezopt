# EzOpt
マラソン中に手軽にハイパーパラメータ探索をするためのツール

- Before
    - 「あれ，ここの `float hoge = 0.7;` という定数，もう少し大きな値にしたほうがスコアが伸びるかもしれないぞ」
    - （`float hoge = 0.8;` に変更して上書き保存）
    - `g++ main.cpp && ./a.out < in.txt`
    - （`Score: 1134` と出力される）
    - 「おーちょっと改善してんじゃん」
    - （`float hoge = 0.9;`に変更して上書き保存）
    - `g++ main.cpp && ./a.out < in.txt`
    - （`Score: 871` と出力される）
    - 「あー今度はだいぶ下がったな．一番スコアが良くなるところはどこだろう？じゃあ 0.75 だとどうかなあ」
    - （`float hoge = 0.75;`に変更して上書き保存）
    - `g++ main.cpp && ./a.out < in.txt`
    - （`Score: 1029` と出力される）
    - ......（以下，延々と手動調整）

- After
    - 「あれ，ここの `float hoge = 0.7;` という定数，もう少し大きな値にしたほうがスコアが伸びるかもしれないぞ」
    - （`float hoge = (0.7)/* HP: 0.7 -- 1.0 */;` に変更して上書き保存）
    - `ezopt "g++ main.cpp && ./a.out < in.txt" --maximize`

## Dependencies

- Python >= 3.10

## Install
```sh
pip install -e .
```

## Usage

### 使用例
```sh
ezopt "g++ examples/main.cpp && ./a.out" --minimize --value-pattern "Score: (.+)"
```
これにより，後述の「ハイパーパラメータ記述フォーマット」で
`examples/main.cpp` 内に記述されたハイパーパラメータたちを
最適化することができます．
- `--minimize` を指定しているので，目的関数の値の「最小化」を目指します．
- `--value-pattern "Score: (.+)"` の指定により，`Score: ...` の形式で出力されている箇所が目的関数の値と認識されます．マッチ箇所が複数ある場合は，それらを「集約」（デフォルトでは「合計」）したものが目的関数の値と認識されます．
    - なお，`--value-pattern` のデフォルト値は `"Score: (.+)"` であるため（AHC 準拠），実際にはこのオプション指定は不要です．

### 一般的な使用法

```sh
usage: ezopt [-h] [-p VALUE_PATTERN] [-M] [-m] [-g] [-n TRIALS] [-a {sum,sumlog}] [-o OUTPUT_DIR] CMD

EZOPT: Easy Optimization

positional arguments:
  CMD                   Command to run. Example: 'g++ main.cpp && ./a.out < in.txt'

options:
  -h, --help            show this help message and exit
  -p VALUE_PATTERN, --value-pattern VALUE_PATTERN
                        Pattern to extract value
  -M, --maximize        Maximize the value
  -m, --minimize        Minimize the value
  -g, --grid            Grid search mode
  -n TRIALS, --trials TRIALS
                        Number of trials
  -a {sum,sumlog}, --aggregation {sum,sumlog}
                        How to aggregate values from multiple matches
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory
```
- CMD 部分には 一度だけ `〜.cpp` という表現が含まれる必要があります．

### ハイパーパラメータ記述フォーマット

cpp ファイルの中で，ハイパーパラメータは以下のように記述します．
```cpp
...
    float x = (3.0)/* HP : 1.0 -- 4.0 */;
...
```
この記述は，上記ソース内の `3.0` の部分がハイパーパラメータであり，その値の探索範囲が 1.0 以上 4.0 以下であることを表します．

一般的な書式は以下の通りです：

```
(<置き換えたい部分>) /* <HPの名前> : <探索範囲> */
```
- 「置き換えたい部分」には，`(` や `)` を追加で含むことはできません．
- 「HPの名前」の部分は，`HP` で始まりかつ空白文字を含まない文字列を任意に指定できます．重複がある場合，重複しないように勝手にリネームされます．
- 「探索範囲」の部分は，以下のいずれかの書式に従ってください．
    1. `<下限値> -- <上限値>`: 下限値以上・上限値以下の値を，一様サンプリングにより探索します．
    2. `<下限値> --- <上限値>`: 下限値以上・上限値以下の値を，対数スケールで一様サンプリングにより探索します．
    3. `[<値1>, <値2>, ..., <値N>]`: 指定された有限個の値を，カテゴリカルな扱いで一様に探索します．

