# EzOpt
マラソン中に手軽にハイパーパラメータ探索をするためのツール

## Dependencies

- Python >= 3.10

## Install
```sh
pip install -e .
```

## Usage

### 使用例
```sh
ezopt "g++ examples/main.cpp && ./a.out"
```
これにより，後述の「ハイパーパラメータ記述フォーマット」で
`examples/main.cpp` 内に記述されたハイパーパラメータの
組み合わせを全通り試すことができます．


### 一般的な使用法

```sh
ezopt "cmd"
```
ここで cmd 部分には 一度だけ `〜.cpp` という表現が含まれる必要があります．
上記コマンドによって，「当該 cpp ファイルのハイパーパラメータ部分をさまざまに変更した場合の cmd」を
全通り実行することができます（並列実行ではありません）．

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

