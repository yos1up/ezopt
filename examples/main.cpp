#include<bits/stdc++.h>
using namespace std;

int main(){
    float a = (33.4) /* //HP:[33.4, 7.1, 9.8]*/;
    int b = (62) /* //HP: [60]*/;
    bool c = (true) /* //HP_hoge: [true, false]*/;
    float coef = (0.774) /*HP: 0.0 -- 1.0*/;
    float coef2 = (0.334) /* HP: 0.1 --- 10.0*/;
    cout << "Hello World!" << endl;
    cout << "Score: " << pow(coef - 0.7, 2) + pow(coef2 - 1.8, 1.3) << endl;
    cout << b << endl;
    return 0;
}
