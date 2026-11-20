//midi音乐
#include <bits/stdc++.h>
#include <Windows.h>
#pragma comment(lib,"winmm.lib")
using namespace std;

enum Scale//定义音符和乐速 
{
    Rest = 0, C8 = 108, B7 = 107, A7s = 106, A7 = 105, G7s = 104, G7 = 103, F7s = 102, F7 = 101, E7 = 100,
    D7s = 99, D7 = 98, C7s = 97, C7 = 96, B6 = 95, A6s = 94, A6 = 93, G6s = 92, G6 = 91, F6s = 90, F6 = 89,
    E6 = 88, D6s = 87, D6 = 86, C6s = 85, C6 = 84, B5 = 83, A5s = 82, A5 = 81, G5s = 80, G5 = 79, F5s = 78,
    F5 = 77, E5 = 76, D5s = 75, D5 = 74, C5s = 73, C5 = 72, B4 = 71, A4s = 70, A4 = 69, G4s = 68, G4 = 67,
    F4s = 66, F4 = 65, E4 = 64, D4s = 63, D4 = 62, C4s = 61, C4 = 60, B3 = 59, A3s = 58, A3 = 57, G3s = 56,
    G3 = 55, F3s = 54, F3 = 53, E3 = 52, D3s = 51, D3 = 50, C3s = 49, C3 = 48, B2 = 47, A2s = 46, A2 = 45,
    G2s = 44, G2 = 43, F2s = 42, F2 = 41, E2 = 40, D2s = 39, D2 = 38, C2s = 37, C2 = 36, B1 = 35, A1s = 34,
    A1 = 33, G1s = 32, G1 = 31, F1s = 30, F1 = 29, E1 = 28, D1s = 27, D1 = 26, C1s = 25, C1 = 24, B0 = 23,
    A0s = 22, A0 = 21
};

enum Voice//音符 
{
    X1 = C2, X2 = D2, X3 = E2, X4 = F2, X5 = G2, X6 = A2, X7 = B2,
    L1 = C3, L2 = D3, L3 = E3, L4 = F3, L5 = G3, L6 = A3, L7 = B3,
    M1 = C4, M2 = D4, M3 = E4, M4 = F4, M5 = G4, M6 = A4, M7 = B4,
    H1 = C5, H2 = D5, H3 = E5, H4 = F5, H5 = G5, H6 = A5, H7 = B5,
    LOW_SPEED = 500, MIDDLE_SPEED = 400, HIGH_SPEED = 300,
    _ = 0XFF
};

void PlayMusic(int music[],int size)//播放音乐函数 
{
	HMIDIOUT handle;
	midiOutOpen(&handle,0,0,0,CALLBACK_NULL);
 
	int volume=0x7f;
	int voice=0x0;
	int sleep=1000;
 
	for (int i=0;i<size;i++)
	{
		int note=music[i];
 
		if (note==LOW_SPEED || note==HIGH_SPEED || note==MIDDLE_SPEED)
		{
			sleep=note;
			continue;
		}
 
		if (note==0)
		{
			sleep=175;
			continue;
		}
 
		if (note==700)
		{
			Sleep(175);
			continue;
		}
 
		if (note==_)
		{
			Sleep(500);
			continue;
		}
 
		voice = (volume << 16) + ((note) << 8)+0x90;
		midiOutShortMsg(handle,voice);
		std::cout << voice << std::endl;
		Sleep(sleep);
	}
	midiOutClose(handle);
}

//以下是音乐乐谱
int kju[]=
{
	L1,_,L1,_,L1,_,L1,_,L1,_,L1,_,X7,_,L3,_,_,L2,_,L1,_,X7,_,X6,_,_,_,
	L3,_,L3,_,L3,_,L3,_,L3,_,L3,_,L5,_,_,L4,_,L2,_,L4,_,L3,_,_,_,
	L6,_,L6,_,L6,_,L6,_,L6,_,L6,_,L5,_,L5,_,L3,_,L4,_,L5,_,_,_,
	L4,_,L3,_,L2,_,_,L2,_,L2,_,L2,_,L2,_,L3,_,L3,_,_,_,
	M1,_,_,L7,_,_,L6,_,_,_,
	L5,_,L6,_,L7,_,L7,_,L7,_,_,_,
	L6,_,L6,_,L6,_,_,L5,_,L5,_,L5,_,L6,_,L5,_,L4,_,L3,_,_,_,
	M1,_,_,L7,_,_,L6,_,_,_,
	L7,_,L6,_,L7,_,L7,_,L7,_,_,_,
	L3,_,L3,_,L3,_,_,L7,_,L7,_,M1,_,L7,_,L6,_,_,_,
};//《We Will Follow Him Only》乐谱 

int kji[]=
{
	L3,_,_,L2,_,L1,_,L2,_,L3,_,L4,_,_,_,
	X7,_,X7,_,L3,_,_,L2,_,X6,_,_,_,
	L5,_,_,L4,_,L3,_,L4,_,L5,_,L6,_,_,_,
	L2,_,L2,_,L5,_,_,L4,_,L3,_,_,_,
	M1,_,_,L7,_,L6,_,L3,_,_,L4,_,L5,_,_,_,
	L6,_,L7,_,L6,_,_,L5,_,L2,_,_,_,
	L6,_,_,L3,_,L1,_,L2,_,L3,_,L4,_,_,_,
	L3,_,L3,_,L7,_,_,L3,_,L6,_,_,_,
};//《No Motherland Without You》乐谱

int NKarmy[]=
{
	L3,_,
};//《Song of North Korean People's Army》乐谱 

int attack[]=
{
	L4,_,
};//《攻击战》乐谱

int CCCP[]=
{
	L5,_,
};

int flowlight[]=
{
	L3,_,_,L3,_,L2,_,L3,_,_,L3,_,L2,_,L3,_,_,L5,_,L5,_,_,_,
	L1,_,L1,_,L2,_,L3,_,_,L3,_,L2,_,L3,_,_,L3,_,L2,_,L3,_,L5,_,_,L5,_,_,_,
	L5,_,L6,_,L5,_,L6,_,M1,_,M1,_,L6,_,_,_,
	L6,_,L5,_,L6,_,L5,_,L3,_,_,_,
	L3,_,L2,_,L3,_,L5,_,L3,_,L2,_,L1,_,_,L3,_,L2,_,_,_,
	L3,_,L2,_,L3,_,_,L3,_,L2,_,L3,_,_,L3,_,L2,_,L3,_,L5,_,_,L5,_,_,_,
	L1,_,L1,_,L2,_,L3,_,_,L3,_,L2,_,L3,_,_,L3,_,L2,_,L3,_,L6,_,_,L5,_,_,_,
	L5,_,L5,_,L6,_,M1,_,L6,_,L6,_,L5,_,L6,_,_,_,
	L5,_,L3,_,L3,_,L2,_,L3,_,L5,_,L1,_,_,L2,_,_,_,
	L6,_,_,L5,_,M3,_,_,M2,_,_,L5,_,_,L6,_,M3,_,_,M2,_,_,_,
	L5,_,L5,_,M5,_,M2,_,_,M1,_,_,L5,_,L5,_,M5,_,M2,_,_,M1,_,_,_,
	M1,_,M1,_,L6,_,L5,_,L6,_,M1,_,_,_,
	L5,_,L6,_,M1,_,M3,_,M2,_,M2,_,M1,_,_,_,
	L5,_,L6,_,M1,_,M3,_,M2,_,M2,_,M1,_,M1,_,L6,_,M1,_,M3,_,M2,_,_,_,
	L5,_,L6,_,M1,_,M5,_,M3,_,M2,_,M3,_,M2,_,M1,_,M1,_,L6,_,L5,_,L6,_,M1,_,M2,_,M3,_,_,_,
	M5,_,_,M3,_,M2,_,M3,_,M2,_,M1,_,M1,_,L6,_,L5,_,L6,_,M1,_,M3,_,M2,M1,_,_,_,
	M3,_,M2,_,M1,_,M1,_,L6,_,M1,_,_,_,
	M5,_,_,M1,_,M1,_,L6,_,M1,_,_,_,
	L5,_,L6,_,M1,_,M3,_,M2,_,M2,_,M1,_,M1,_,L6,_,M1,_,M3,_,_,M2,_,_,_,
	L5,_,L6,_,M1,_,M5,_,M3,_,M2,_,M3,_,M2,_,M1,_,M1,_,L6,_,L5,_,L6,_,M1,_,M2,_,M3,_,_,_,
	M5,_,_,M3,_,M2,_,M3,_,M2,_,M1,_,M1,_,L6,_,L5,_,L6,_,M1,_,M3,_,M2,M1,_,_,_,
	M3,_,M2,_,M1,_,M1,_,L6,_,M1,_,_,_,
	M5,_,_,M1,_,M1,_,L6,_,M1,_,M3,M2,_,_,M2,_,_,_,
	M3,_,M5,_,M3,_,M2,M1,_,M1,_,M1,_,_,_,
};

int Klee[]=
{
	L3,_,_,L3,_,_,_,
	L3,_,L3,_,L3,_,L4,_,L4,_,_,_,
};

void song_list()//音乐列表 
{
	cout << "歌曲列表:" << endl;
	cout << "1--We Will Follow Him Only" << endl
		 << "2--No Motherland Without You" << endl
		 << "3--Song of North Korean People's Army" << endl
		 << "4--攻击战" << endl
		 << "5--National Anthem of CCCP" << endl
		 << "6--流光记" << endl
		 << "7--真红骑士，出发" << endl;
}

void midi_menu()//操作 
{
	cout << "输入数字选择播放的歌曲" << endl;
	song_list();
	int choice,size=0;
	cin >> choice;
	switch(choice)//可判断输入的选项，也可以规避掉不正确的输入 
	{
		case 1:
		{
			size=sizeof(kju)/sizeof(kju[0]);
			PlayMusic(kju,size);
			break;
		}
		case 2:
		{
			size=sizeof(kji)/sizeof(kji[0]);
			PlayMusic(kji,size);
			break;
		}
		case 3:
		{
			size=sizeof(NKarmy)/sizeof(NKarmy[0]);
			PlayMusic(NKarmy,size);
			break;
		}
		case 4:
		{
			size=sizeof(attack)/sizeof(attack[0]);
			PlayMusic(attack,size);
			break;
		}
		case 5:
		{
			size=sizeof(CCCP)/sizeof(CCCP[0]);
			PlayMusic(CCCP,size);
			break;
		}
		case 6:
		{
			size=sizeof(flowlight)/sizeof(flowlight[0]);
			PlayMusic(flowlight,size);
			break;
		}
		case 7:
		{
			size=sizeof(Klee)/sizeof(Klee[0]);
			PlayMusic(Klee,size);
			break;
		}
		default:
		{
			cout << "输入错误，请重新输入" << endl;
		}//不正确的输入可以被排除在外 
	}
}

int main()
{
	cout << "----------------------" << endl
		 << "       MIDI音乐       " << endl; 
	midi_menu();
	system("pause");
	return 0;
}
