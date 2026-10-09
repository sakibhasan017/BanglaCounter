// Exact word-level normalized Levenshtein similarity against training responses.
// Input: N_train N_models N_test, then token-ID sequences, one per line.
// Output: each test output's maximum similarity to a training response.
#include <algorithm>
#include <iomanip>
#include <iostream>
#include <vector>
using namespace std;

using Seq = vector<int>;
Seq readseq() {
    int n; cin >> n;
    Seq s(n);
    for (int &x : s) cin >> x;
    return s;
}
int distance(const Seq &a, const Seq &b) {
    vector<int> prev(b.size()+1), cur(b.size()+1);
    for (size_t j=0;j<prev.size();++j) prev[j]=int(j);
    for (size_t i=1;i<=a.size();++i) {
        cur[0]=int(i);
        for (size_t j=1;j<=b.size();++j)
            cur[j]=min({prev[j]+1,cur[j-1]+1,prev[j-1]+(a[i-1]!=b[j-1])});
        prev.swap(cur);
    }
    return prev.back();
}
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int ntrain,nmodels,ntest;
    cin >> ntrain >> nmodels >> ntest;
    vector<Seq> train(ntrain);
    for (auto &s:train) s=readseq();
    cout << fixed << setprecision(12);
    for (int m=0;m<nmodels;++m) for (int i=0;i<ntest;++i) {
        Seq q=readseq();
        double best=0;
        for (const auto &r:train) {
            size_t den=max(q.size(),r.size());
            double sim=den ? 1.0-double(distance(q,r))/double(den) : 1.0;
            if (sim>best) best=sim;
        }
        cout << m << ' ' << i << ' ' << best << '\n';
    }
}
