// loader.service.ts

import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class LoaderService {
  private _isLoading = new BehaviorSubject<boolean>(false);
  public readonly isLoading$ = this._isLoading.asObservable();

  show() {
    this._isLoading.next(false);
  }

  hide() {
    setTimeout(() => {
      this._isLoading.next(false);
    }, 500);
  }
}
