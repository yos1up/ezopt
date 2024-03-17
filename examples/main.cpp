#include<bits/stdc++.h>
using namespace std;

int main(){
    float a = (33.4) /* //HP:[33.4, 7.1, 9.8]*/;
    int b = (62) /* //HP: [60]*/;
    bool c = (true) /* //HP_hoge: [true, false]*/;
    float coef = (0.774) /*HP: 0.0 -- 1.0*/;
    float coef2 = (0.334) /* HP: 0.1 --- 10.0*/;
    float coef3 = (33.4) /* HP: [1.2, 3.4, 5.6]*/;
    float coef4 = (0.0) /*HP: -3.0 -- 3.0 */; // 無関係な変数
    cout << "Hello World!" << endl;
    cout << "Score: " << pow(coef - 0.7, 2) + pow(coef2 - 1.8, 2) + pow(coef3 - 4, 2) << endl;
    cout << b << endl;
    return 0;
}
